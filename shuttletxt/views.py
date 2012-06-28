from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from shuttletxt.models import Shuttle, ShuttleStop, RouteCoordinate
import urllib, re, math, datetime, logging
from django.db.models import Q

AT_STOP_DIST = .0006	 # distance from a stop a bus can be to be "at" that stop
ON_ROUTE_DIST = .002	 # distance before we declare that a bus is confused / lost
WEST_ROUTE = ['Student Union','Footbridge','15th and College','Polytech Apartments','Blitman Residence Commons','9th and Sage','West Hall','Sage']
EAST_ROUTE = [u'Student Union',u'Colonie Apartments',u'Brinsmade Terrace',u'Beman Lane',u'Sunset Terrace',u'BARH',u'9th and Sage',u'West Hall', u'Sage']

WEST_EXCLUSIVE = ('Footbridge', 'Polytech Apartments', 'Blitman Residence Commons', '15th and College')
EAST_EXCLUSIVE = ('BARH','Sunset Terrace','Beman Lane','Colonie Apartments', 'Brinsmade Terrace')

def index(request):
	logging.debug('index')
	return render_to_response( 'index.html', {'hello':'index!'} )

@csrf_exempt
def accept_event(request):
	active_shuttles = get_shuttles()
	if not active_shuttles:
		return HttpResponse(' The system is having some hiccups. Please let me know at mcmilj@rpi.edu. Thanks.', mimetype="text/plain")
	
	if request.method == 'POST' and request.POST:
		route_request = request.POST['body'].lower()
	else:
		route_request = request.GET['body'].lower()

	if 'e' in route_request[0]:
		route_request = 'east'
	if 'w' in route_request[0]:
		route_request = 'west'
	if route_request not in ('east','west'):
		return HttpResponse('Proper syntax: redhawk e[ast] OR redhawk w[est]', mimetype="text/plain")
   
	text_string = responder(route_request)
			
	#else:
#		text_string = responder('east')
	#	text_string = 'East: ' + responder('east') + '\n' + 'West: ' + responder('west')
	
	if text_string:
		return HttpResponse(text_string, mimetype="text/plain")
	else:
		return HttpResponse(' No active shuttles (that have their GPS enabled!).', mimetype="text/plain")
	
def get_shuttles():
	try:
		filehandle = urllib.urlopen('http://shuttles.rpi.edu/vehicles/current.kml')
	except:
		logging.critical('Ohhh boy. Could not reach current.kml')
		return False

	whole_file = filehandle.read()
	buses = re.findall('<name>Bus [0-9]+</name>', whole_file)
	coordinates = re.findall('[-]?[0-9]+[.][0-9]+', whole_file)
	
	i = 0
	bus_near = []
	
	for i in xrange(len(buses)):		# From <name>Bus [0-9]+</name> to just Bus ##
		buses[i] = buses[i][6:-7]
	
	all_shuttles = Shuttle.objects.all()
	for shuttle in all_shuttles:
		if shuttle.name not in buses:
			shuttle.active = False
		else:
			shuttle.active = True
		shuttle.save();
	
	i = 0
	for bus in buses:
		if i < len(coordinates)-1:
			longitude = coordinates[i]
			latitude = coordinates[i+1]
			i = i + 2
			
			all_stops = ShuttleStop.objects.all()
			try:
				bus_record = Shuttle.objects.get(name=bus)
			except:
				logging.error('There\'s a new shuttle in town, dude:'+bus)
				return
			bus_record.current_lat = latitude
			bus_record.current_long = longitude
			bus_record.save()
			
			for stop in all_stops:
				dist_bus_to_stop = distance(stop.latitude, stop.longitude, bus_record.current_lat, bus_record.current_long)
				if dist_bus_to_stop < AT_STOP_DIST:
					bus_record.east_west = check_east_west(stop.name, bus_record.east_west)
					bus_record.last_stop = stop.name
					bus_near.append(bus + ": "+ stop.name)
					break
					
			bus_record.save()
				
	return True
	
def responder(route_request):
	route_shuttles = Shuttle.objects.filter(east_west=route_request).filter(active=True)
	text_string = ''
	for shuttle in route_shuttles:
		stop = ShuttleStop.objects.get(name=shuttle.last_stop)
		next_stop = ''
		
		if shuttle_parked(shuttle):	 # shuttle is parked
			text_string += shuttle.name + ' seems parked\n'
			continue
		elif not ensure_shuttle_on_a_route(shuttle):		# shuttle is not on normal route
			text_string += shuttle.name + ' seems to be off normal route\n'
			continue
		else:   # shuttle is ensured to be on a route
			pass
		
		if route_request == 'west':
			WRi = WEST_ROUTE.index(stop.name)
			if WRi == len(WEST_ROUTE)-1:
				next_stop = WEST_ROUTE[0]
			else:
				next_stop = WEST_ROUTE[WRi+1]
				
		elif route_request == 'east':
			ERi = EAST_ROUTE.index(str(stop.name))
			if ERi == len(EAST_ROUTE)-1:
				next_stop = EAST_ROUTE[0]
			else:
				next_stop = EAST_ROUTE[ERi+1]
		
		try:
			stop_next_stop = ShuttleStop.objects.get(name=next_stop)
			stop_last_stop = ShuttleStop.objects.get(id=shuttle.last_stop)
			last_stop_string = str(stop_last_stop.name)
		except:
			return 'Something troubling occurred'
		
		dist_bus_to_last_stop = distance(stop.latitude, stop.longitude, shuttle.current_lat, shuttle.current_long)
		dist_bus_to_next_stop = distance(stop_next_stop.latitude, stop_next_stop.longitude, shuttle.current_lat, shuttle.current_long)
		dist_last_stop_to_next_stop = distance(stop.latitude, stop.longitude, stop_next_stop.latitude, stop_next_stop.longitude)
		
		logging.debug ('Dist bus to last stop: ' + str(dist_bus_to_last_stop))
		logging.debug ('Dist last stop to next: ' + str(dist_last_stop_to_next_stop))
		logging.debug ('Div of those two: ' + str(math.fabs(dist_bus_to_last_stop - dist_last_stop_to_next_stop)))
		
		if dist_bus_to_last_stop < AT_STOP_DIST:
			text_string += shuttle.name + ' is at ' + shuttle.last_stop + '\n'
		elif math.fabs(dist_last_stop_to_next_stop - dist_bus_to_next_stop) < .25 * dist_last_stop_to_next_stop:
			text_string += shuttle.name + ' is leaving ' + shuttle.last_stop + '\n'
		elif math.fabs(dist_last_stop_to_next_stop - dist_bus_to_last_stop) < .25 * dist_last_stop_to_next_stop:
			text_string += shuttle.name + ' is approaching ' + stop_next_stop.name +'\n'
		else:
			text_string += shuttle.name + ' is between ' + last_stop_string + ' and ' + next_stop + '\n'		   
			
	return text_string
	

def check_east_west(stop_name, old_east_west):
	if stop_name in WEST_EXCLUSIVE:
		return 'west'
	elif stop_name in EAST_EXCLUSIVE:
		return 'east'
	else:
		return old_east_west
	
def distance(latitude1, longitude1, latitude2, longitude2):
	lat_dist = math.fabs(float(latitude2)) - math.fabs(float(latitude1))
	long_dist = math.fabs(float(longitude2)) - math.fabs(float(longitude1))
	dist = math.sqrt(math.pow(lat_dist,2)+math.pow(long_dist,2))
	return dist
	
def ensure_shuttle_on_a_route(shuttle):
	shuttle_last_loc = ShuttleStop.objects.get(name=shuttle.last_stop)
	assumed_path = RouteCoordinate.objects.filter(Q(last_loc=shuttle_last_loc.id) | Q(last_loc=0))
	for point in assumed_path:
		if (distance(point.latitude, point.longitude, shuttle.current_lat, shuttle.current_long) < ON_ROUTE_DIST):
			return True
		else:
			pass

	all_points_in_routes = RouteCoordinate.objects.exclude(east_west='park')
	for point in all_points_in_routes:
		if (distance(point.latitude, point.longitude, shuttle.current_lat, shuttle.current_long) < ON_ROUTE_DIST):
			shuttle.last_stop = ShuttleStop.objects.get(id=point.last_loc)
			shuttle.east_west = point.east_west
			shuttle.save()
			return True
		else:
			pass
			
	return False

def shuttle_parked(shuttle):
	all_points_parking = RouteCoordinate.objects.filter(last_loc=99)
	for point in all_points_parking:
		if (distance(point.latitude, point.longitude, shuttle.current_lat, shuttle.current_long) < AT_STOP_DIST):
			return True
		else:
			pass
	return False
