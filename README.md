
Working commute lamentation
the solution: computatation

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

Further Reading:
* http://web.mta.info/nyct/facts/ridership/#chart_s
* http://web.mta.info/nyct/facts/ridership/ridership_sub.htm
