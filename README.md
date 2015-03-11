
Subway reliability has been down recently. We bitch and whine, but what can we actually do?

We can make smarter decisions, but for that we need better data and tools.

So, the MTA has an [API to tracks trains](http://apps.mta.info/traintime/)
and it can be used to generate [pretty visualizations](http://www.livetrain.nyc/)

But the MTA isn't a *train* company, it's a *people-mover*.
It should track people moving through the system!

Why? Because trains running doesn't mean they're moving people well:

1. the trains could be moving slowly
2. they could be already full by the time they arrive
3. your platform may be so backed up that you can't get on the next train anyway
4. they may arrive on time and dump you off before you actually get to your destination

Instead of measuring *trains* they should [measure *actual travel time*
between various destinations](https://ipnetwork.bgtmo.ip.att.net/pws/network_delay.html).

So that's what I want to do -- to instrument people's smartphones as they
travel through the city, especially on the subway and especially during
rush hour; because I want to improve my own commute time, and the first
step is to gather data on it.

Travel Vectors
Trav
travel options

L 4
De[kalb Ave]
Bo[wling Green]

Further Reading:
* [AT&T Network Latency chart](https://ipnetwork.bgtmo.ip.att.net/pws/network_delay.html)
* http://web.mta.info/nyct/facts/ridership/#chart_s
* http://web.mta.info/nyct/facts/ridership/ridership_sub.htm
* http://www.straphangers.org/statesub14/
* [Livetrain.nyc](http://www.livetrain.nyc/)
* [Waze](https://www.waze.com/livemap)

Reference:
* https://en.wikipedia.org/wiki/List_of_New_York_City_Subway_lines#Nomenclature
* https://en.wikipedia.org/wiki/IRT_Broadway_%E2%80%93_Seventh_Avenue_Line
* https://en.wikipedia.org/wiki/Bus_bunching

Travel Options:
* MTA bus
* MTA train
* NYC Taxi
* Uber
* Citibike
* Car rental (Hertz, Enterprise, etc)
* Short-term car rental (ZipCar, Hertz 24/7, etc)
* https://www.erideshare.com/carpool.php?dstate=NY
* http://www.nywatertaxi.com/
* http://www.nycgo.com/articles/nyc-transportation-getting-around
* http://www.hubcab.org/#13.00/40.7272/-73.9303

http://web.mta.info/developers/developer-data-terms.html#data

Service Status - refreshed every minute
http://web.mta.info/status/serviceStatus.txt

New York City Transit Subway - Updated December 04, 2014
http://web.mta.info/developers/data/nyct/subway/google_transit.zip

http://datamine.mta.info/
http://datamine.mta.info/sites/all/files/pdfs/nyct-subway.proto.txt
http://datamine.mta.info/mta_esi.php?key=bbd484ca89540588c3dfdf88d6af15a0
