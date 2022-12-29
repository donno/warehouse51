////////////////////////////////////////////////////////////////////////////////
//
//  XBMC Media Stream Protocol Server
//
//  A media stream server, which implements XBMSP (XB Media Streaming Protocol)
//
//  Version: 0.0.1
//
////////////////////////////////////////////////////////////////////////////////
//  Copyright 2011 Sean Donnellan <darkdonno@gmail.com>
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
////////////////////////////////////////////////////////////////////////////////



// Client packets
#define XBMSP_PACKET_NULL                      10
#define XBMSP_PACKET_SETCWD                    11
#define XBMSP_PACKET_FILELIST_OPEN             12
#define XBMSP_PACKET_FILELIST_READ             13
#define XBMSP_PACKET_FILE_INFO                 14
#define XBMSP_PACKET_FILE_OPEN                 15
#define XBMSP_PACKET_FILE_READ                 16
#define XBMSP_PACKET_FILE_SEEK                 17
#define XBMSP_PACKET_CLOSE                     18
#define XBMSP_PACKET_CLOSE_ALL                 19
#define XBMSP_PACKET_SET_CONFIGURATION_OPTION  20
#define XBMSP_PACKET_AUTHENTICATION_INIT       21
#define XBMSP_PACKET_AUTHENTICATE              22
#define XBMSP_PACKET_UPCWD                     23

// Server packet types

#define XBMSP_PACKET_OK                         1
#define XBMSP_PACKET_ERROR                      2
#define XBMSP_PACKET_HANDLE                     3
#define XBMSP_PACKET_FILE_DATA                  4
#define XBMSP_PACKET_FILE_CONTENTS              5
#define XBMSP_PACKET_AUTHENTICATION_CONTINUE    6


/*
  Development Notes:

  On Windows with MSVC requires /EHsc /ID:\Programs\Development\boost_1_44_0\
*/

#include <boost/bind.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/enable_shared_from_this.hpp>
#include <boost/asio.hpp>

#include <stdio.h>

//#include <typeinfo>
#define PROTOCOL_VERSION "XBMSP-1.0 1.0, "
#define ON_CONNECTION_STRING PROTOCOL_VERSION "Donno's XBMPS Media Server 0.0.1"

using boost::asio::ip::tcp;

int max_length = 1024;

class session
{
public:
  session(boost::asio::io_service& io_service)
    : socket_(io_service)
  {
  }

  tcp::socket& socket()
  {
    return socket_;
  }

  void start()
  {
    // Write out version infomation
    boost::asio::async_write(socket_,
      boost::asio::buffer(ON_CONNECTION_STRING),
      boost::bind(&session::handle_write, this,
        boost::asio::placeholders::error));

    socket_.async_read_some(boost::asio::buffer(data_, max_length),
        boost::bind(&session::handle_read, this,
          boost::asio::placeholders::error,
          boost::asio::placeholders::bytes_transferred));
  }

  void handle_read(const boost::system::error_code& error,
      size_t bytes_transferred)
  {
    if (!error)
    {
      data_[bytes_transferred] = '\0';
      printf("incoming: %s\n", data_);
      boost::asio::async_write(socket_,
          boost::asio::buffer(data_, bytes_transferred),
          boost::bind(&session::handle_write, this,
            boost::asio::placeholders::error));
    }
    else
    {
      printf("Error\n");
      delete this;
    }
  }

  void handle_write(const boost::system::error_code& error)
  {
    if (!error)
    {
      socket_.async_read_some(boost::asio::buffer(data_, max_length),
          boost::bind(&session::handle_read, this,
            boost::asio::placeholders::error,
            boost::asio::placeholders::bytes_transferred));
    }
    else
    {
      printf("Error\n");
      delete this;
    }
  }

private:
  tcp::socket socket_;
  enum { max_length = 1024 };
  char data_[max_length];
};

class Server
{
public:
  Server(boost::asio::io_service& io_service, short port)
    : myIo_service(io_service),
      myAcceptor(io_service, tcp::endpoint(tcp::v4(), port))
  {
    session* new_session = new session(myIo_service);
    myAcceptor.async_accept(new_session->socket(),
        boost::bind(&Server::handle_accept, this, new_session,
          boost::asio::placeholders::error));
  }

  void handle_accept(session* new_session,
      const boost::system::error_code& error)
  {
    if (!error)
    {
      new_session->start();
      new_session = new session(myIo_service);
      myAcceptor.async_accept(new_session->socket(),
          boost::bind(&Server::handle_accept, this, new_session,
            boost::asio::placeholders::error));
    }
    else
    {
      printf("Error: handle_accept\n");
      delete new_session;
    }
  }

private:
  boost::asio::io_service& myIo_service;
  tcp::acceptor myAcceptor;
};

int main(int argc, char* argv[])
{
  printf("XBMC Media Stream Protocol Server 0.0.1\n");
  boost::asio::io_service io_service;
  try
  {
    Server server(io_service, 1400);
    io_service.run();
  }
  catch (std::exception& e)
  {
    fprintf(stderr, "%s\n", e.what());
  }
  return 0;
}
