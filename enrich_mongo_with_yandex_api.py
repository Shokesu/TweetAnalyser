from geopy.geocoders import Yandex
from geopy.exc import GeocoderTimedOut
from pymongo import MongoClient

try:

    geolocator = Yandex(lang='en_US')
    counter_general = 0
    counter_not_having_location = 0
    counter_already_enriched = 0
    counter_already_loc_api_error = 0
    counter_api_call = 0
    counter_yandex_api_no_result_call = 0
    counter_yandex_api_has_result_call = 0
    client = MongoClient('localhost:27017')
    db = client.TweetScraper

    for month in range(1, 13):
        mymonth = str(month).rjust(2, '0')
        for day in range(1, 32):
            myday = str(day).rjust(2, '0')
            for hour in range(0, 24):
                myhour = str(hour).rjust(2, '0')
                for min in range(0, 60):
                    mymin = str(min).rjust(2, '0')
                    for sec in range(0, 60):
                        mysec = str(sec).rjust(2, '0')
                        filterdate = "2016-" + str(mymonth) + "-" + str(myday) + " " + str(myhour) + ":" + str(
                            mymin) + ":" + str(mysec)
                        # res = db.tweet.find_one({"ID":"815355320516153344"})

                        for res in db.tweet.find({"datetime": filterdate}):
                            try:

                                if res is None:
                                    break

                                if counter_api_call == 24950:
                                    print("terminated. counter_api_call == 25000")
                                    break;


                                counter_general = counter_general + 1
                                if "tw_enr_country" in res.keys():
                                    counter_already_enriched = counter_already_enriched + 1
                                    print("already enriched with yandex. counter_already_enriched:" + str(counter_already_enriched))
                                    continue
                                elif "loc_res" in res.keys():
                                    counter_already_loc_api_error = counter_already_loc_api_error + 1
                                    print("already has yandex error. counter_already_loc_api_error:" + str(counter_already_loc_api_error))
                                    continue

                                geocode_result = None
                                if res["tw_coordinates"] is not None:
                                    tweet_coordinates = res["tw_coordinates"].get('coordinates')
                                    lat = tweet_coordinates[1]
                                    lon = tweet_coordinates[0]
                                    coordinates = str(lat) + "," + str(lon)

                                    counter_api_call = counter_api_call + 1
                                    #reverse api call
                                    geocode_result = geolocator.reverse(coordinates, exactly_one=True, timeout=None)
                                    if geocode_result is None or len(geocode_result) == 0:
                                        db.tweet.update({"ID": res["ID"]}, {"$set": {"loc_res": '1'}})
                                        continue;

                                elif res["tw_loc_country"] is not None and res["tw_loc_name"] is not None:
                                    tweet_country = res["tw_loc_country"]
                                    tweet_loc_name = res["tw_loc_name"]
                                    user_location = tweet_country + " " + tweet_loc_name

                                    counter_api_call = counter_api_call + 1
                                    #geocode api call
                                    geocode_result = geolocator.geocode(user_location, exactly_one=True, timeout=None)
                                    if geocode_result is None or len(geocode_result) == 0:
                                        db.tweet.update({"ID": res["ID"]}, {"$set": {"loc_res": '2'}})
                                        continue;

                                elif res["user_location"] is not None and res["user_location"] != '' and res["user_geo_enabled"] is True:
                                    user_location = res["user_location"]

                                    counter_api_call = counter_api_call + 1
                                    # geocode api call
                                    geocode_result = geolocator.geocode(user_location, exactly_one=True, timeout=None)
                                    if geocode_result is None or len(geocode_result) == 0:
                                        db.tweet.update({"ID": res["ID"]}, {"$set": {"loc_res": '3'}})
                                        continue;

                                else:
                                    counter_not_having_location = counter_not_having_location + 1
                                    print("counter_not_having_location: " + str(counter_not_having_location) + " " +  str(res))
                                    continue;

                                # api call is completed

                                if geocode_result is not None and len(geocode_result) != 0:
                                    raw = geocode_result.raw
                                    rawmetadata = raw["metaDataProperty"]
                                    rawmetadataproperty = rawmetadata["GeocoderMetaData"]
                                    addressdetails = rawmetadataproperty["AddressDetails"]
                                    country = addressdetails["Country"]
                                    countryname = country["CountryName"]

                                    if countryname is not None and len(countryname) != 0:
                                        counter_yandex_api_has_result_call = counter_yandex_api_has_result_call + 1
                                        print("success result for yandex api call. counter_yandex_api_has_result_call" + str(counter_yandex_api_has_result_call))
                                        db.tweet.update({"ID": res["ID"]}, {"$set": {"tw_enr_country": countryname}})
                                    else:
                                        counter_yandex_api_no_result_call = counter_yandex_api_no_result_call + 1
                                        print("there is no result for reverse api call. counter_yandex_api_no_result_call:" + str(counter_yandex_api_no_result_call))
                                        db.tweet.update({"ID": res["ID"]}, {"$set": {"loc_res": '4'}})

                                else:
                                    db.tweet.update({"ID": res["ID"]}, {"$set": {"loc_res": '5'}})

                            except GeocoderTimedOut as exception:
                                print('Oops!  An error occurred.  Try again... line: ', exception)

                            except Exception as exception:
                                #db.tweet.update({"ID": res["ID"]}, {"$set": {"loc_res": '6'}})
                                print('Oops!  An error occurred in loop.  Try again... line: ', exception)

except Exception as exception:
    print('Oops!  An error occurred.  Try again...', exception)

print("counter_general,counter_not_having_location,counter_already_enriched,counter_already_loc_api_error,counter_api_call,counter_yandex_api_no_result_call,counter_yandex_api_has_result_call:" + str(counter_general) + "," + str(counter_not_having_location) + "," + str(counter_already_enriched) + "," + str(counter_already_loc_api_error) + "," + str(counter_api_call) + "," + str(counter_yandex_api_no_result_call) + "," + str(counter_yandex_api_has_result_call))

# Geocoding an address
