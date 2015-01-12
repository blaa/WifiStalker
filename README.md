# Wording

Trying to name things:

Sender / Host - any 802.11 transmitter
Client - wifi client, probably a mobile device, also: Station
AP - access point
Knowledge - aggregated information on Senders.
Event - seeing a client on the ether for a period of time.

# Features

## Sniffer

Separate process sniffing metadata from Wifi packets and storing
them in MongoDB backend. Can use multiple sniffers with the same
backends each with differently tagged location.

Gathers metadata from radiotap (strength, source, destination),
Dot11, Dot11Elt frames (probe request, response, beacons) and for
not encrypted packets from IP/TCP/UDP frames (source, destination,
protocol, DNS queries) - for a highlevel aggregation can certainly
be improved.

## Analyzer

Parses packets stored in the collection by sniffers and updates
the \`knowledge' about access points (AP) and clients - senders.

Knowledge consists of:

-   user supllied metadata (alias, owner, notes)
-   simple statistics, first seen, last seen metadata
-   device vendor from MAC database
-   Recent signal strength reading (running average)
-   Probed SSIDs
-   Beaconed SSIDs
-   AP geolocation data using openwlan database
-   \`Events' - when host was seen, TODO: Needs better handling

## Web interface

-   Clickable, interactive web application created with AngularJS,
    Bootstrap and other - ChartJS.
-   Observing surroundings within specified time window (10s - 24h)
-   Creating presence snapshots - currently present clients (within time
    window) on the context of surrounding APs.
-   Investigating details about each sniffed node.

## Marauder's Map

-   Select point on map and store information about surrounding
    stations (their macs and average strength from a time window)
-   Display all stored points
-   TODO: Estimate position on map using stored info.

# How to use

## Start Mongo, create monitoring interface (iwconfig wlan0 mode monitor or airmon-ng start wlan1 )

## Data sources / initialization:

wget <http://www.ieee.org/netstorage/standards/oui.txt>
wget &#x2013;no-check-certificate 'https://openwlanmap.org/db.tar.bz2'
./wifistalker &#x2013;load-geo db/&#x2026;
Vendors currently loaded on each start - FIXME.

## Start sniffing process wifistalker -s

You can name it with -l sniffer<sub>name</sub>. Not really usable at this
point, but useful to distinguish parallel sniffers - they create a
separate presence context.

## Start analyzing process - wifistalker -a

## Start webapp - wifistalker -w

## Open page in your browser to see results.

## Tips:

Theoretically you can start multiple sniffers with different labels
pointed to the same mongodb backend. Run only single analyzer
thread.

If you don't purge \`all<sub>frames'</sub> table you can reanalyze your whole
Knowledge.

You can sniff with a detached device and then merge all<sub>frames</sub>
tables into one (TODO: There should be an easy option for
that). You can sniff using a device in a backpack and access it
using different channel (bluetooth/other wifi) to use webapp on a
mobile (TODO: Check how it works on mobile, TODO: Check for
sniffing options on an Android).

Sniffer requires root, rest of modes should run on less privileged
user.

## Concept

Sniffed data can be split into mobile (mostly) client devices and
background - beacons. Beacons create context which is usable to
determining location

## Reasons to write

Learning AngularJS and Bootstrap. Curiosity. Extending home alarm
with a wifi-based monitoring against a common robbery.

# LICENSE

Backend is licensed under GNU GPLv2 - mostly because it uses GPLv2
Scapy. Frontend license might vary, it will probably be MIT.

# TODOs / Plan:

## TODO Cleanup code, publish on github, add license

## Sniffer

### TODO Sniff for higher layers - IP, etc. And gather additional metadata.

### TODO Detect automatically outlier packets

### TODO Intelligent channel hopping / client following

Aggregating beacons is simple, when sniffing for a client packet
prelong a visit on a specified channel to sniff more of client
communication - because of power savings those happen in bursts.

### TODO I like using timestamps but datetime would probably be better.

## Timetable / knowledge book

### TODO ESSID tab - all clients calling this essid.

### TODO Viewing and comparison of presence snapshots, existance in a presence dump

### TODO Sorting and filtering for time table.

### TODO Refresh interval selection.

### DONE Create a service for diagram which shows better information.

### DONE Knowledge book - page with details on cli/ap

### DONE Return knowledge as an array, not dict, and sort in different ways.

### Charts

1.  TODO Add time range for strength chart

2.  TODO Add refresh button

3.  TODO Add graph display of relations.

## Marauder's Map

### Allow selecting BSSID in Map view and then placing it on map.

### Localization services for map.

-   Dump place (almost works)
-   Dumped places (show)
-   Add map, change image
-   Show current sniffer localizations
-   IDEA: Rewind history and display different localizations (\`seen' on a map)

## TODO Config view

Allow for changing:
-   Seen algorithm parameters
-   Purge all<sub>frames</sub>
-   Get DB stats

## Analyzer

### Idea: Allow to mark specified time range as a sniffing in a particular location

Then - automatically mark all bssids as located within this
localization (home, work, tram, shop)

### TODO \`event/Seen' knowledge should contain a context - visible BSSID during seeing.

### TODO Fix \`event/seen' algorithm - nice parametrized filtering.

### TODO Events should contain stamp of highest signal strength.

### TODO If more time passed than current<sub>frames</sub> keep - use all<sub>frames</sub> for initialization automatically

## Map

### Map image changing / location changing.

### Point removal

### Placing Stations by click on the map.

## Logs

### Display controller on all views on the navbar