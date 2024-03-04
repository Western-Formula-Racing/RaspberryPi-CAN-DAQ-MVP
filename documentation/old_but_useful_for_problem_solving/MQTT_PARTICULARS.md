# Update March 3, 2024
MQTT and Grafana work fine now. Max data points doesn't matter that much. The key for stability with Grafana visualizations with MQTT as the data source is to make sure the time interval is sufficiently short (I've had luck with "now-20s" absolute time range) and turn auto refresh off. This sucks for InfluxDB-based visualizations because they require auto refresh to update. Maybe two separate dashboards can be created for InfluxDB-based visualizations and MQTT-based visualizations.

Auto refresh can be turned off at done at the dashboard-level, not the visualization level:
<img src="https://gist.github.com/assets/70295347/fc5f5680-5812-4f94-ab66-8e8513501d13" width="800">

# MQTT + Grafana is Tumultuous
This combination of technologies is particularly cumbersome and fragile in its current state. 

## Solution to broken time recording intervals/many other problems
The solution was to make sure ALL time intervals (the main grafana one at the top of the dashboard, and all individual graph time intervals) are set to now-5 minutes, and then use systemctl to restart grafana-server.service: `sudo systemctl restart grafana-server.service`. Just do this if recording gets weird.

## Why is this a tumultuous combination?
The way Grafana renders data - I believe - is based on in-browser caching of datapoints. When you refresh, the cache is cleared. 

For data sources that are stationary, like databases, this is no problem, because the query can be made to the database and get all the info that was previously displayed. With streaming sources with transient data, though, this cannot happen, because the data is not stored anywhere and is just broadcasted when canInterface receives it. 

As well, Grafana caching relies heavily on the time interval you're trying to display. In MQTT when selecting it as a data source for a graph, it has fields called "Max data points", which is the maximum number of data points Grafana will display in the graph. For gauges from a streaming data source, you would think that Grafana would just display the newest values so the cache would always just remain of size 1, but it actually insidiously stores the MQTT messages, so max data points still applies and has an effect.

When data points displayed/cached > max data points, Grafana stops querying from the data source. Simple solution right? Increase max data points? Yeah, it doesn't work. I honestly don't know why. I have found it most stable when leaving it as auto calculating the max data points displayed, and just letting Grafana figure it out. But even then, sometimes values just... stop? 

## Very tentative solution to random stopping
Sometimes, if there is no information displaying on the graphs driven by MQTT, editing the relevant graphs and using the "query inspector" tool:

<img src="https://user-images.githubusercontent.com/70295347/235187678-7719d0f4-3018-41ea-bba4-519ac81beb13.png" width="600">
<img src="https://user-images.githubusercontent.com/70295347/235187885-80f2880c-2d1f-432d-b0a0-7b0c107c4543.png" width="400">



to refresh the query sometimes will get things moving again. But still, the problem with time points remains. There is consistency to the time period recorded before stopping, so surely there is a solution to this?  