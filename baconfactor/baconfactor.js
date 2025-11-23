// Run convertNames.js first to generate this file.
import { actorNames, titleNames } from "./names.generated.js";

// Define an index for looking up the associate between actors and shows or
// shows and actors.
//
// File format for index or mappings is:
// - Four byte header:
//   * Magic number: 0xbf (bactorfactor)
//   * File version: 0x01 - Version 1
//   * File features: 1 byte (0 for links are IDs and 1 for links are indices)
//   * Reserved     : 1 byte - ignored.
// - Source Count : u32
// - Source ID 0
// - ...
// - Destination Count : u32  (this is at (Source Count) * 4 bytes) after..
// - Offset for destination of first source.
// - Offset for destination of second source.
// - ...
// - Destination count for Source[0]
// - Destination[0] for Source[0]
// - Destination[1] for Source[0]
// - Destination[Count0 - 1] for Source[0]
// - Destination count for Source[1]
// - Destination[0] for Source[1]
// - Destination[1] for Source[1]
// - Destination[Count1 - 1] for Source[1]
//
// The reason it was this way rather than [Start, Count], [Start, Count]
// is lost. The other approach I've seen used by Boost is to have the Count be
// implicit, where you know [OffsetToA, OffsetToB,...] that OffsetToA ends at
// OffsetToB so the count is implicit.
//
// The source IDs are also included but they are ignored as they assumed to
// be in the lists instead to be able to map to names.
//
// This logic is encoded in the Index class.
class Index {
  constructor(sources, links) {
    this.sources = sources;
    this.links = links;
  }

  // Return the index of the given source given their ID.
  indexById(id)
  {
    return this.sources.indexOf(id);
  }

  // Return the connection for the source at the given index.
  //
  // The connections are the indices rather than IDs.
  connections(index) {
    const connectionOffset = this.links[index];
    const connectionCount = this.links[connectionOffset];
    return this.links.slice(connectionOffset + 1,
                            connectionOffset + connectionCount + 1);
  }

  // Create an Index object from a buffer.
  //
  // This can read the index of mapping actors to shows or shows to actors.
  static fromBuffer(buffer) {
    // File format for index or mappings is:
    //
    // Four byte header:
    // * Magic number: 0xbf (bactorfactor)
    // * File version: 0x01 - Version 1
    // * File features: 1 byte (0 for links are IDs and 1 for links are indices)
    // * Reserved     : 1 byte - ignored.
    //
    // Followed by source count (u32) then source IDs, then total destination
    // count/ (u32) then the offsets for each source to the count of
    // destinations from that source and then the destinations.
    const data = new Uint32Array(buffer);
    const header = data[0];
    // The header is ignored for now - and assume feature is links are indices.
    const sourceCount = data[1];
    const targetCount = data[1 + sourceCount];
    return new Index(data.slice(2, 2 + sourceCount),
                     data.slice(3 + sourceCount));
  }

  // Create Index object from a file fetched from a URL.
  // This can read the index of mapping actors to shows or shows to actors.
  static async fetch(url) {
    const response = await fetch(url);
    const buffer = await response.arrayBuffer();
    return Index.fromBuffer(buffer);
  }
}

// Store the data.
class Data {
  constructor(actors, titles, actorsToTitles, titlesToActors) {
    this.actors = actors;
    this.titles = titles;
    this.actorsToTitles = actorsToTitles;
    this.titlesToActors = titlesToActors;
  }

  // Return the index for the actor given their ID.
  actorIndexById(id)
  {
    return this.actors["ids"].indexOf(id);
  }
  
  // Return the ID for the actor at the given index.
  actorId(index)
  {
    return this.actors["ids"][index];
  }

  // Return the name for the actor at the given index.
  actorName(index)
  {
    return this.actors["names"][index];
  }

  // Return the index for the show given its ID.
  showIndexById(id)
  {
    return this.titles["ids"].indexOf(id);
  }

  // Return the ID for the show at the given index.
  showId(index)
  {
    return this.titles["ids"][index];
  }

  // Return the name for the show at the given index.
  showName(index)
  {
    return this.titles["names"][index];
  }

  // Return the names of the shows with the given indices.
  showNames(indices)
  {
    // Indices is often a slice of Uint32Array, and map() doesn't work as 
    // expected on that, so use forEach() instead.
    const names = this.titles["names"];
    var resolvedNames = [];
    indices.forEach((index) => resolvedNames.push(names[index]));
    return resolvedNames;
  }
  
  // Return the indices of shows that the given actor (by index) is in.
  //
  // The result is the show's index.
  showsForActors(index) {
    return this.actorsToTitles.connections(index);
  }

  // Return the indices of actors that in the given show (by index).
  //
  // The result is the actors' index.
  actorsInShows(index) {
    return this.titlesToActors.connections(index);
  }
}

export function findSequence(startShowId, endShowId, data)
{
  const startShowIndex = data.showIndexById(startShowId);
  const endShowIndex = data.showIndexById(endShowId);
  return findSequenceByIndices(startShowIndex, endShowIndex, data );
}

export function findSequenceByIndices(startShowIndex, endShowIndex, data)
{
  var visitedShowIndices = new Set();

  var queue = [{"sequence": [startShowIndex]}];
  while (queue.length)
  {
    var node = queue.shift();
    const actors = data.actorsInShows(node.sequence[node.sequence.length - 1]);
    node.sequence.push(0); // Place holder for the next actor in the sequence.

    // For each actor that appeared in the show,
    // find what shows they were in.
    const keepGoing = actors.every((actorIndex) => {
      const shows = data.showsForActors(actorIndex);

      // Update the actor index in the sequence.
      node.sequence[node.sequence.length - 1] = actorIndex;

      // Check to find out if we are the end.
      if (shows.find((show) => show == endShowIndex))
      {
        node.sequence.push(endShowIndex);
        return false;
      }

      // Now each show the actor was in needs to be visited if we haven't
      // didn't find it.
      shows.forEach((showIndex) => {
        if (!visitedShowIndices.has(showIndex))
        {
          // Add the new show to the queue.
          let newSequence = node.sequence.slice();
          newSequence.push(showIndex);
          queue.push({"sequence": newSequence});

          // Mark it as visited now so if another actori s also in the show it
          // is ignored.
          visitedShowIndices.add(showIndex);
        }
      });
            
      return true;
    });

    // If one of the actors was in the end show, then we don't keep going and 
    // we have found the a sequence between the shows.
    if (!keepGoing)
    {
      return node.sequence;
    }
  }
  return [];
}

// Resolve the sequence to the names (and IDs).
export function resolveSequence(sequence, data)
{
  return sequence.map((element, index) => {
    if (index & 1)
    {  
      const name = data.actorName(element);
      const id = data.actorId(element);
      return `${name} (${id})`
    }
    const name = data.showName(element);
    const id = data.showId(element);
    return `${name} (${id})`
  })
}

export async function loadData()
{
  // Decode the data.
  let actorsToTitles, titlesToActors;
  if (typeof window === 'undefined')
  {
    [actorsToTitles, titlesToActors] = await Promise.all([
      Index.fetch(new URL('../data/actors_to_titles.dat', import.meta.url)),
      Index.fetch(new URL('../data/titles_to_actors.dat', import.meta.url)),
    ]);
  }
  else
  {
    [actorsToTitles, titlesToActors] = await Promise.all([
      Index.fetch(new URL('actors_to_titles.dat', import.meta.url)),
      Index.fetch(new URL('titles_to_actors.dat', import.meta.url)),
    ]);
  }
  const actors = {"ids": actorsToTitles.sources, "names": actorNames};
  const titles = {"ids": titlesToActors.sources, "names": titleNames};
  return new Data(actors, titles, actorsToTitles, titlesToActors);
}
