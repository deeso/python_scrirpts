import urllib 
import urllib2 

import threading

BaseProp = 361995
EndProp = 362044

proxies = {'http': 'http://localhost:8080'}

# handles getting the owner pdf listing of the home
class DoNothingRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):   
        return  headers

opener = urllib2.build_opener(DoNothingRedirectHandler())
data_sheet_url = 'http://.org/appraisal/publicaccess/PropertyDataSheet.aspx?PropertyID=%s&PropertyOwnerID=%s&NodeID=11'
get_data_location = lambda propId,ownerId:  opener.open(urllib2.Request(data_sheet_url%(propId, ownerId)))
get_data_pdf = lambda url: urllib.urlopen(url).read()

def get_pdf_listing(propId, ownerId, owner_name):
	fname = owner_name.replace(" ","_").replace(",","").replace("&","and")+".pdf"
	x = get_data_location(propId, ownerId)
	if x.headers:
		url = x.getheader('Location')
		if url == "":
			return
		url = "http://.org/"+url.split("#")[0]
		pdf = get_data_pdf(url)
		f = open(fname,'wb')
		f.write(pdf)
		print "wrote pdf", fname
	


MAIN_HISTORY = {}
PropIds = []
for i in xrange(BaseProp, EndProp):
	PropIds.append('R%d'%i)


CurrentYear = 2010
EndYear = 2006
	
history_url =  "http://.org/appraisal/publicaccess/PropertyHistory.aspx?PropertyID=%s&PropertyOwnerID=%s&NodeID=11&FirstTaxYear=%d&LastTaxYear=%d"

get_history_page = lambda propId,ownerId,eyear,syear:urllib.urlopen(history_url%(propId,ownerId,syear,eyear)).read()

HistorySplit = lambda data: "".join(data.split('<HistoryResults>')[1]).split('</HistoryResults>')[0].strip()
HistoryTaxYearSplit = lambda data: data.split('History TaxYear="')[1].split('" ')[0].strip()
HistroyNameSplit = lambda data: data.split('Name="')[1].split('" ')[0].strip()
HistroyValueSplit = lambda data: data.split('Value="')[1].split('" ')[0].strip()

def process_history(propId,ownerId, cyear, eyear):
	history_data = {}
	page_data = get_history_page(propId,ownerId,  cyear-1, eyear)
	if page_data.find("<HistoryResults>") == -1:
		print "page has no relevant history"
		return {}
	for line in HistorySplit(page_data).splitlines():
		if line.find("History TaxYear=") == -1:
			continue
		line = line.strip()
		if line == "":
			continue
		year = HistoryTaxYearSplit(line)
		name = HistroyNameSplit(line)
		value = HistroyValueSplit(line)
		if not year in history_data:
			history_data[year] = {}
		history_data[year][name] = value
	return history_data


# get the required segments for the square footages and ammendments
init_imp_page = 'http://.org/appraisal/publicaccess/PropertyImpDetail.aspx?CurrPosition=1&LastPosition=1&PropertyID=%s&PropertyOwnerID=0&NodeID=11'
extract_segments = lambda data: int(data.split('<td class="ssDetailLabel" nowrap="true">Segments</td><td class="ssDetailData" nowrap="true">')[1].split("</td>")[0])
get_segments = lambda propId: extract_segments(urllib.urlopen(init_imp_page%propId).read())

segments_url = "http://.org/appraisal/publicaccess/PropertyImpSegDetail.aspx"
segments_data = lambda current,last,propID: "CurrSegPosition=%d&LastSegPosition=%d&CurrPosition=1&LastPosition=1&TaxYear=2008&PropertyID=%s&PropertyOwnerID=0&NodeID=11&dbKeyAuth=Appraisal"%(current,last,propID)
segments_post = lambda data:urllib.urlopen(segments_url,data=data).read()

def traverse_segments(start, end, propId):
	imps = {"MA (Main Area)":"Main Floor", 
			"MA2.0 (Main Area 2nd Flr)":"Second Floor",
			"Garage":"Garage",
			"Porch":"Porch"}
	functions = {"Second Floor":[SecondFlrSqSplit, SecondFlrVaSplit],
				"Main Floor":[MainFlrSqSplit, MainFlrVaSplit],
				"Porch":[PorchFlrSqSplit, PorchFlrVaSplit],
				"Garage":[GarageFlrSqSplit, GarageFlrVaSplit]}
	results = {}
	for i in xrange(start, end+1):
		data = segments_data(i,end,propId)
		page_data = segments_post(data)
		for i in imps.keys():
			if page_data.find(i) > -1:
				name = imps[i]
				results[name+" SQ Footage"] = functions[name][0](page_data).strip()
				results[name+" Value"] = "$"+functions[name][1](page_data).split('$')[1].strip() 
				break
	return results

	
	

header_string = "Address,Name,ID,Legal Description,Year,% inc,Value,Land ($),sq ft,$/sq ft,House ($),Sq ft,$/sq ft,1st floor ($),Sq ft,$/sq ft,2nd floor ($),Sq ft,$/sq ft,Garage ($),Sq ft,$/sq ft,Porch ($),Sq ft,$/sq ft"

split_str2 = '%s:</td><td class="ssDetailData" valign="top">'
split_field2 = lambda sstr, data: data.split(split_str2%sstr)[1].split("</td>")[0]


split_str3 = '<td class="ssDetailLabel">%s:</td><td class="ssDetailData" width="125px" align="right">'
def split_field3(sstr, data):
	return data.split(split_str3)[1].split('&nbsp')[0]

ExemptionSplit = lambda data: data.split('Exemption Codes:</label></td><td><table cellpadding="0" cellspacing="0"><tr><td class="ssDetailData">')[1].split('</td></tr></table></td></tr><tr xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:tyl="http://www.tsgweb.com"><td id="tdEntity" class="ssDetailLabel" valign="top">')[0]
Exemptions = lambda data: ",".join([i.split('(')[0].strip() for i in ExemptionSplit(data).split(" <br />")])

CleanupAddr = lambda addr: addr.replace("<br />","")
# pull out address name, etc on first page
AddrSplit = lambda data: CleanupAddr(data.split('Property Address:</td><td class="ssDetailData" valign="top">')[1].split('</td>')[0])

NameSplit = lambda data: data.split('Owner Name:</td><td class="ssDetailData">')[1].split('</td>')[0].replace("&amp;","&")
YearSplit = lambda data:"2010"

PropID = lambda data: data.split('Property Detail Sheet (')[1].split(')')[0]
LDescSplit = lambda data: data.split('Legal Description:</td><td class="ssDetailData">')[1].split('</td>')[0]

# Pull out values from summary stuff
AppraisedSplit = lambda data: data.split('Appraised:</td><td class="ssDetailData" width="125px" align="right">')[1].split('&nbsp')[0]
LandHSSplit = lambda data: data.split('Land HS:</td><td class="ssDetailData" width="125px" align="right">')[1].split('&nbsp')[0]
ImprovementHSSplit = lambda data: data.split('Improvement HS:</td><td class="ssDetailData" width="125px" align="right">')[1].split('&nbsp')[0]
HomeSteadCapSplit = lambda data: data.split('Homestead Cap:</td><td class="ssDetailData" width="125px" align="right">')[1].split('&nbsp')[0]
AssessedSplit = lambda data: data.split('Assessed:</td><td class="ssDetailData" width="125px" align="right">')[1].split('&nbsp')[0]
OwnerIdSplit = lambda data: data.split('Owner ID:</td><td class="ssDetailData">')[1].split('</td>')[0]

# Pull out values and areas of floors
split_str = '<td class="ssDetailPageLabel" nowrap="1">%s</td><td class="ssDetailPageData" nowrap="1">'
split_field = lambda sstr, data: data.split(split_str %sstr)[1].split('</td>')[0]

MainFlrSqSplit = lambda data: split_field("Area", data)
MainFlrVaSplit = lambda data: split_field("Value", data)

SecondFlrSqSplit = lambda data: split_field("Area", data)
SecondFlrVaSplit = lambda data: split_field("Value", data)

PorchFlrSqSplit = lambda data: split_field("Area", data)
PorchFlrVaSplit = lambda data: split_field("Value", data)

GarageFlrSqSplit = lambda data: split_field("Area", data)
GarageFlrVaSplit = lambda data: split_field("Value", data)


main_url = 'http://.org/appraisal/publicaccess/PropertyDetail.aspx?PropertyID=%s&dbKeyAuth=Appraisal&TaxYear=%s&NodeID=11&PropertyOwnerID=%s'

get_main_page = lambda propId,cyear,ownerId: urllib.urlopen(main_url%(propId, cyear,ownerId), proxies=proxies).read()


THREADS = []

main_search = "http://.org/appraisal/publicaccess/PropertySearch.aspx?PropertySearchType=1&SelectedItem=10&PropertyID=&PropertyOwnerID=&NodeID=11"
search_data = lambda prop_value,cyear: "PropertyID=%s&PropertySearchType=1&NodeID=11&dbKeyAuth=Appraisal&TaxYear=%s&SearchSubmit=Search"%(prop_value, cyear)
get_property = lambda data: urllib.urlopen("http://.org/appraisal/publicaccess/PropertySearchResults.aspx",data=data).read()

def get_propId(property,cyear):
	d = search_data(property,cyear)
	#print d
	page = get_property(d)
	#print page
	print page.split("ViewPropertyOrOwners(")[1].split(")")[0].replace(",","").split()
	propId = page.split("ViewPropertyOrOwners(")[1].split(")")[0].replace(",","").split()[-1].strip()
	ownerId = page.split("ViewPropertyOrOwners(")[1].split(")")[0].replace(",","").split()[-2].strip()
	print "Identified PropertyId: ", propId, "OwnerId: ", ownerId
	return propId, ownerId

	
imp_url = 'http://.org/appraisal/publicaccess/PropertyImpDetail.aspx?CurrPosition=%d&LastPosition=4&PropertyID=%s&PropertyOwnerID=%s&NodeID=11'

def get_rland_sf(propId,ownerId):
	url_str = 'http://.org/appraisal/publicaccess/PropertyLandDetail.aspx?CurrPosition=2&LastPosition=2&PropertyID=%s&PropertyOwnerID=%s&NodeID=11'
	pdata = urllib.urlopen(url_str%(propId,ownerId)).read()
	sz_str = 'Size - Square Feet</td><td class="ssDetailPageData" nowrap="1">'
	value = pdata.split(sz_str)[1].split("</td>")[0]
	return value
	
def get_land_sf(propId,ownerId):
	url_str = 'http://.org/appraisal/publicaccess/PropertyLandDetail.aspx?CurrPosition=1&LastPosition=2&PropertyID=%s&PropertyOwnerID=%s&NodeID=11'
	pdata = urllib.urlopen(url_str%(propId,ownerId)).read()
	sz_str = 'Size - Square Feet</td><td class="ssDetailPageData" nowrap="1">'
	value = pdata.split(sz_str)[1].split("</td>")[0]
	return value

def get_improvements(propId, ownerId, pdata):
	x = pdata.split(' class="ssPropertyLink" style="color:#194274; font-weight:bolder;">Imp')
	imp = {}
	value_str = '''class="ssPropertyLink" style="color:#194274; font-weight:bolder;">Imp'''
	if x > 1:
		value = pdata.split(value_str)[1].split("$")[1].split("</td>")[0].strip()
		imp["Improvements 1"] = "$"+value
	if x > 2:
		# url = imp_url%(2,propId, ownerId)
		# data = urllib.urlopen(url).read()
		# print data.split(value_str)
		# value = data.split(value_str)[1].split("</td>")[0].strip()
		# value = "$"+value.replace("$","").strip()
		# imp["Improvements 2"] = value
		value = pdata.split(value_str)[2].split("$")[1].split("</td>")[0].strip()
		imp["Improvements 2"] = "$"+value
	elif x > 3:
		# url = imp_url%(3,propId, ownerId)
		# data = urllib.urlopen(url).read()
		# value = data.split(value_str)[1].split("</td>")[0].strip()
		# value = "$"+value.replace("$","").strip()
		# imp["Improvements 3"] = value
		value = pdata.split(value_str)[3].split("$")[1].split("</td>")[0].strip()
		imp["Improvements 3"] = "$"+value
	elif x > 4:
		# url = imp_url%(4,propId, ownerId)
		# data = urllib.urlopen(url).read()
		# value = data.split(value_str)[1].split("</td>")[0].strip()
		# value = "$"+value.replace("$","").strip()
		# imp["Improvements 4"] = value
		pass
	return imp
	
PrimarySite = 'S1 (Primary Site)</td><td align="left" nowrap="true" style="overflow-x:hidden;" class="ssDataColumn">A1 (A1 - Residential Single Family)</td><td align="left" nowrap="true" class="ssDataColumn"></td><td align="right" nowrap="true" class="ssDataColumn">'
ResidualLand = 'S3 (Residual Land)</td><td align="left" nowrap="true" style="overflow-x:hidden;" class="ssDataColumn">A1 (A1 - Residential Single Family)</td><td align="left" nowrap="true" class="ssDataColumn"></td><td align="right" nowrap="true" class="ssDataColumn">'



def parse_main_page(main_store, property, cyear='2010'):
	propId,ownerId_sql = get_propId(property,cyear)
	page_data = get_main_page(propId,cyear, ownerId_sql)
	#page_data = open("page.txt").read()
	addr = AddrSplit(page_data)
	ownerName = NameSplit(page_data)
	print "Owner Name:", ownerName
	g = threading.Thread(target=get_pdf_listing, args=(propId,ownerId_sql,ownerName))
	g.start()
	THREADS.append(g)
	ownerid = OwnerIdSplit(page_data)
	print "Owner Id:", ownerid
	#property = PropID(page_data)
	#print property
	ldesc = LDescSplit(page_data)
	# Pull out values from summary stuff
	print "Legal Desc: ",ldesc
	appraised = AppraisedSplit(page_data).strip()
	landHS = LandHSSplit(page_data).strip()
	improveHS = ImprovementHSSplit(page_data).strip()
	hsCap = HomeSteadCapSplit(page_data).strip()
	assessed = AssessedSplit(page_data).strip()
	exemptions = Exemptions(page_data)
	residual = '$'+page_data.split(ResidualLand)[1].split("</td></tr>")[0].split("$")[1].strip()
	primary = '$'+page_data.split(PrimarySite)[1].split("</td></tr>")[0].split("$")[1].strip()
	primarySiteSq = get_land_sf(propId, ownerId_sql)
	residualSq = get_rland_sf(propId, ownerId_sql)
	if property not in main_store:
		main_store[property] = {}
	if not cyear in main_store[property]:
		main_store[property][cyear] = {}
	# get the properties history of values 
	previous_years = process_history(propId, ownerId_sql, int(cyear),2006)
	for year in previous_years:
		main_store[property][year] = previous_years[year]
	
	# add in the prop values for this year
	main_store[property][cyear]['AppraisedValue'] = appraised 
	main_store[property][cyear]['Land HS'] = landHS 
	main_store[property][cyear]['Improvement HS'] = improveHS 
	main_store[property][cyear]['HSCapAdj'] = hsCap
	main_store[property][cyear]['Assessed'] = assessed
	main_store[property][cyear]['Primary Site Value'] = primary
	main_store[property][cyear]['Primary Site SQ'] = primarySiteSq
	main_store[property][cyear]['Residual Land Value'] = residual
	main_store[property][cyear]['Residual Land SQ'] = residualSq
	main_store[property][cyear]['Exemptions'] = exemptions
	# Get various floor SQ footage
	segments = get_segments(propId)
	improvements = traverse_segments(1, segments, propId)
	#improvements = {}
	
	imp = get_improvements(propId, ownerId_sql, page_data)
	if len(imp) > 0:
		for i in imp:
			main_store[property][cyear][i] = imp[i]
	
	for year in main_store[property].keys():
		main_store[property][year]['Year']  = year
		main_store[property][year]['Property']  = property
		main_store[property][year]['Owner Id']  = ownerid
		main_store[property][year]['Address']  = addr
		main_store[property][year]['Owner Name'] =ownerName 
		main_store[property][year]['Property ID'] = property
		main_store[property][year]['Legal Description'] = ldesc
		main_store[property][year]['Primary Site SQ'] = primarySiteSq
		main_store[property][year]['Residual Land SQ'] = residualSq
		for segment in improvements.keys():
			# do not have previous year improvements
			if segment.find("Value") > -1 and year == cyear:
				main_store[property][year][segment] = improvements[segment]
			elif segment.find("Value") == -1:
				main_store[property][year][segment] = improvements[segment]
	return main_store
	
csv_str = '''Address,Owner Name,Owner Id,Property ID,Legal Description,Year,Improvement HS,Land HS,AppraisedValue,HSCapAdj,Assessed,First Floor SQ Footage,First Floor Value,Second Floor SQ Footage,Second Floor Value,Garage SQ Footage,Garage Value,Porch SQ Footage,Porch Value,Improvements 1,Improvements 2,Improvements 3,Primary Site SQ,Primary Site Value,Residual Land SQ,Residual Land Value'''

def write_csv(dict_of_props):
	global csv_str
	csv_list = csv_str.split(",")
	data_strs = []
	for property in dict_of_props.keys():
		for year in dict_of_props[property].keys():
			items = []
			for item in csv_list:
				if item in dict_of_props[property][year]:
					items.append('"'+dict_of_props[property][year][item]+'"')
			data_strs.append(",".join(items))
	print "\n".join(data_strs)
	return data_strs
	
	
def join_all_pending_thread(threads):
	for i in threads:
		if i.isAlive():
			print "Waiting on thread"
			t.join()
	threads.clear()
	return threads

	
