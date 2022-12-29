//===----------------------------------------------------------------------===//
//
// spotifyscrobbler - Submit music being listened to on the Spotify desktop
// client to Last.fm via the Last.fm Desktop client.
//
// This program aims to bridge the hole in Spotify's Last.fm integration
// which doesn't extend to "Spotify Connect", i.e streaming to a Internet
// connected television.
//
// This program has only been developed and tested on Microsoft Windows.
//
//===----------------------------------------------------------------------===//
// 
// How it works:
// - It connects to the Spotify desktop client via HTTP which allows it to
//   determine if Spotify is currently playing music and what music.
// - It then sends this information to the Last.fm desktop client using the
//   ScrobSubmitter classes/portion of the plugins for the Microsoft Windows
//   Desktop client.
//
//===----------------------------------------------------------------------===//
//
// Building:
// The building process is complicated as I wanted to avoid duplicating the
// sources from the Last.fm project.
//
// Libraries required:
//  Winhttp.lib for using WinHttpOpen 
//  shell32.lib for using ShellExecuteA
//  Advapi32.lib for using RegOpenKeyExA/RegQueryValueExA
//
//  cl /nologo /EHsc spotifyscrobbler.cpp ScrobSubmitter.cpp scrobsub.lib shell32.lib Advapi32.lib Winhttp.lib /It
//
//===----------------------------------------------------------------------===//
// Licensing
/* Copyright 2016, Sean Donnellan. <darkdonno@gmail.com>                       
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *     * Neither the name of the <organization> nor the
 *       names of its contributors may be used to endorse or promote products
 *       derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY <copyright holder> ''AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL <copyright holder> BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "ScrobSubmitter.h"

#include <iostream>

// D:\VCS\lastfm-desktop\common\c++\win\scrobSubPipeName.cpp

static void ScrobSubCallback(
  int reqID,
  bool error,
  std::string message,
  void* userData)
{
  std::cout << "Callback: " << message << std::endl;
}

/*
REquest: https://localhost.spotilocal.com:4371/simplecsrf/token.json
Headers: Origin: https://open.spotify.com
REsponse: {'token': <token> }
  token=2f27826200c3c1302ed949252334371e
csrf

Request: https://open.spotify.com/token
Resposnesponse: {'t': <token> }
    {"t":"NAowChgKB1Nwb3RpZnkSABoGmAEByAEBJXk4C1gSFOm-hFW3J6MdRZhTrRJ9EKjWIQPc"}
oauth

https://localhost.spotilocal.com:4371/remote/status.json?oauth=NAowChgKB1Nwb3RpZnkSABoGmAEByAEBJRGpV1gSFCReNgvhzP8U_brxFi3GkYfCiJLA&csrf=2f27826200c3c1302ed949252334371e

*/

#include <Winhttp.h>
#include <stdexcept>
#include <string>

struct Track
{
  std::string title;
  std::string artist;
  std::string album;
  unsigned int length;
  bool playing;
};

const std::string AdvertTitle("$$<>Advert<>$$");

struct SpotifyApiClient
{
  SpotifyApiClient();
  ~SpotifyApiClient();

  void FetchAndStoreTokens();

  Track Status() const;

  std::string FetchCsrfToken() const;
  std::string FetchOauthToken() const;
private:

  HINTERNET mySession;
  HINTERNET myConnection;
  std::string myCsrfToken;
  std::string myOauthToken;
};

void SpotifyApiClient::FetchAndStoreTokens()
{
  myCsrfToken = FetchCsrfToken();
  myOauthToken = FetchOauthToken();
}

SpotifyApiClient::SpotifyApiClient()
: mySession(nullptr),
  myConnection(nullptr)
{
  mySession = WinHttpOpen(
    L"LastFmSpotify/1.0",
    WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
    WINHTTP_NO_PROXY_NAME,
    WINHTTP_NO_PROXY_BYPASS, 0);

  if (mySession)
  {
    myConnection = WinHttpConnect(
      mySession,
      L"localhost.spotilocal.com",
      4371, // This can change for Spotify...
      0);
  }

  if (!myConnection)
  {
    throw std::runtime_error("Unable to connect to Spotify client.");
  }
}

SpotifyApiClient::~SpotifyApiClient()
{
  if (myConnection) WinHttpCloseHandle(myConnection);
  if (mySession) WinHttpCloseHandle(mySession);
}

#include <memory>

#include "picojson.h"

// Read the response from a request after WinHttpReceiveResponse is issued.
std::string ReadResponse(HINTERNET request);

Track SpotifyApiClient::Status() const
{
  const auto path =
    "/remote/status.json?oauth=" + myOauthToken + "&csrf=" + myCsrfToken;

  static int a = [&] { std::cout << path << std::endl; return 5; }();

  int slength = (int)path.length() + 1;
  const auto len = MultiByteToWideChar(CP_ACP, 0, path.c_str(), slength, 0, 0);
  std::unique_ptr<wchar_t[]> pathW(new wchar_t[len]());
  MultiByteToWideChar(CP_ACP, 0, path.c_str(), slength, pathW.get(), len);

  const auto request = WinHttpOpenRequest(
    myConnection,
    L"GET",
    pathW.get(),
   NULL, WINHTTP_NO_REFERER,
   WINHTTP_DEFAULT_ACCEPT_TYPES,
   WINHTTP_FLAG_SECURE);


  if (!request)
  {
    throw std::runtime_error("Unable to fetch Csrf token from Spotify client.");
  }

  auto successful = WinHttpSendRequest(
    request,
    L"Origin: https://open.spotify.com\r\n",
    0, WINHTTP_NO_REQUEST_DATA, 0,
    0, 0);

  if (successful)
    successful = WinHttpReceiveResponse(request, nullptr);

  const auto response = ReadResponse(request);

  if (request) WinHttpCloseHandle(request);

  picojson::value v;
  const std::string err = picojson::parse(v, response);
  if (!err.empty()) std::cerr << err << std::endl;

  if (!v.is<picojson::object>()) {
    std::cerr << "JSON is not an object" << std::endl;
  }

  const auto track = v.get("track");
  if (!track.is<picojson::object>()) {
	  const auto error = v.get("error");
	  if (!error.is<picojson::object>()) {
		  std::cerr << "\"error\" is not a JSON object" << std::endl;
	  }

	  // TODO WRite code and message.
	  std::cerr << response << std::endl;


  }
  const auto length =
    static_cast<unsigned int>(track.get("length").get<double>());

  const auto type = track.get("track_type").to_str();

  if (type == "ad")
  {
    return { AdvertTitle, {}, {}, length, v.get("playing").get<bool>() };
  }

  const auto title = track.get("track_resource").get("name");
  const auto artist = track.get("artist_resource").get("name");
  const auto album = track.get("album_resource").get("name");


  return { title.to_str(), artist.to_str(), album.to_str(), length,
           v.get("playing").get<bool>() };
}

std::string SpotifyApiClient::FetchCsrfToken() const
{
  const auto request = WinHttpOpenRequest(
    myConnection,
    L"GET",
    L"/simplecsrf/token.json",
     NULL, WINHTTP_NO_REFERER,
     WINHTTP_DEFAULT_ACCEPT_TYPES,
     WINHTTP_FLAG_SECURE);


  if (!request)
  {
    throw std::runtime_error("Unable to fetch Csrf token from Spotify client.");
  }

  auto successful = WinHttpSendRequest(
    request,
    L"Origin: https://open.spotify.com\r\n",
    0, WINHTTP_NO_REQUEST_DATA, 0,
    0, 0);

  if (successful)
    successful = WinHttpReceiveResponse(request, nullptr);

  const auto response = ReadResponse(request);

  if (request) WinHttpCloseHandle(request);

  // Find: "token":
  const auto needle = "\"token\": \"";
  const auto start = response.find(needle);
  if (start == std::string::npos)
  {
    std::cerr << "csrf token response: " << response << std::endl;
    throw std::runtime_error("Bad response from Spotify client for CSRF token");
  }

  const auto tokenStart = start + sizeof(needle) + 2;
  const auto tokenEnd = response.find("\"", tokenStart);
  if (tokenEnd == std::string::npos)
  {
    std::cerr << "csrf token response: " << response << std::endl;
    throw std::runtime_error("Bad response from Spotify client for CSRF token");
  }

  return response.substr(tokenStart, tokenEnd - tokenStart);
}

std::string SpotifyApiClient::FetchOauthToken() const
{
  // Visit: https://open.spotify.com/token in a web browser.
  return "NAowChgKB1Nwb3RpZnkSABoGmAEByAEBJZf7nlkSFKxvScYWY6WG5Hvsr6-j2Eucbumy";
  HINTERNET connection;
  if (mySession)
  {
    connection = WinHttpConnect(
      mySession,
      L"open.spotify.com",
      443,
      0);
  }

  if (!connection)
  {
    throw std::runtime_error("Unable to connect to Spotify.");
  }

  const auto request = WinHttpOpenRequest(
    connection,
    L"GET",
    L"/token",
    NULL, WINHTTP_NO_REFERER,
    WINHTTP_DEFAULT_ACCEPT_TYPES,
    WINHTTP_FLAG_SECURE);


  if (!request)
  {
    throw std::runtime_error("Unable to fetch oauth token from Spotify.");
  }

  auto successful = WinHttpSendRequest(
    request,
    L"",
    0, WINHTTP_NO_REQUEST_DATA, 0,
    0, 0);

  if (successful)
    successful = WinHttpReceiveResponse(request, nullptr);

  const auto response = ReadResponse(request);

  // NOTE: ReadResponse can throw so this would leak..
  if (request) WinHttpCloseHandle(request);
  if (connection) WinHttpCloseHandle(connection);

  // ASssume it
  const auto needle = "{\"t\":\"";
  const auto start = response.find(needle);
  if (start == std::string::npos)
  {
    std::cerr << response << std::endl;
    throw std::runtime_error("Bad response from Spotify.");
  }

  const auto end = response.find("\"", start + sizeof(needle));
  if (end == std::string::npos)
  {
    std::cerr << response << std::endl;
    throw std::runtime_error("Bad response from Spotify.");
  }

  return response.substr(start + sizeof(needle), 66);
}

std::string ReadResponse(HINTERNET request)
{
  if (!request) return "<bad request>";

  std::string response;

  // TODO: response needs to be cumlatiive.
  DWORD size;
  do
  {
    // Check for available data.
    size = 0;
    if (!WinHttpQueryDataAvailable( request, &size))
        printf("Error %u in WinHttpQueryDataAvailable.\n", GetLastError());

    if (size == 0) break;

    // Allocate space for the buffer.
    response.resize(size + 1);

    DWORD downloaded;
    if (!WinHttpReadData(request, (LPVOID)&response[0], size, &downloaded))
    {
      printf("Error %u in WinHttpReadData.\n", GetLastError());
    }
  } while (size > 0);

  return response;
}

std::ostream& operator<<(std::ostream& out, const Track& track);

std::ostream& operator<<(std::ostream& out, const Track& track)
{
  out << (track.playing ? "Playing " : "Paused on ");
  if (track.title == AdvertTitle)
  {
    out << "ADVERTISEMENT";
  }
  else
  {
    out << track.title << std::endl << "By " << track.artist << std::endl;
    out << "On " << track.album << std::endl;
  }
  return out;
}

void Submit(const Track& track, ScrobSubmitter* submitter)
{
  // TODO: Track last submitted track and avoid re-submitting.
  static Track last;

  if (last.title == track.title)
  {
    if (last.playing != track.playing)
    {
      std::cout << "Changing playback status...";
      if (track.playing) submitter->Resume();
      else submitter->Pause();
      last = track;
    }
  }
  else
  {
    std::cout << "Starting" << std::endl;
    if (!last.title.empty() && last.playing) submitter->Stop();

    last = track;

    if (track.title != AdvertTitle)
    {
      const auto id = submitter->Start(
        track.artist,
        "", // Album Artist
        track.title,
        track.album,
        "", // ID
        track.length, //Length / Duration
        "",
        ScrobSubmitter::UTF_8);

      if (!track.playing)
      {
        submitter->Pause();
      }
    }
  }
}

int main()
{
  // Spotify API
  SpotifyApiClient spotify;
  spotify.FetchAndStoreTokens();

  std::cout << spotify.FetchCsrfToken() << std::endl;
  std::cout << spotify.FetchOauthToken() << std::endl;

  ScrobSubmitter submitter;

  //submitter.Init("donno-spotify", ScrobSubCallback, nullptr);
  submitter.Init("wmp", ScrobSubCallback, nullptr); // Claim to be WMP just so the client doesn't say "unknown media player"

  while (true)
  {
    const auto track = spotify.Status();
    std::cout << track << std::endl;
    Submit(track, &submitter);
    SleepEx(6000, true);
  }

  submitter.Stop(); // On exit and mark the end of a song.

  return 1;
  const auto id = submitter.Start(
    "Wrabel", // Artist
    "", // Album Artist
    "11 Blocks", // Track
    "", // Album
    "", // ID
    300, //Length / Duration
    "",
    ScrobSubmitter::UTF_8);

  std::string wait;
  std::cout << "Waiting to stop" << std::endl;
  std::cin >> wait;

  submitter.Stop(); // On exit and end of a song.

  return 0;
}
