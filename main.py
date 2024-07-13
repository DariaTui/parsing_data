import requests
from bs4 import BeautifulSoup
import json
from time import strftime
from get_session import session
from datetime import date, timedelta
import schedule
import pymysql.cursors
from config import host,user,password,db_name

url = "https://api.101hotels.com/hotel/available/region/russia/irkutskaya_oblast?"

global date_today
global date_tomorrow 
global data_date
data_date = date.today()
date_today = str(data_date.strftime("%Y")+"-"+data_date.strftime("%m")+"-"+data_date.strftime("%d"))
date_tomorrow = str((data_date+timedelta(days = 1)).strftime("%Y")+"-"+(data_date+timedelta(days = 1)).strftime("%m")+"-"+(data_date+timedelta(days = 1)).strftime("%d"))


def get_data_of_hotels(page):
    params = pass_page_to_params(page)
    response = session.post(url = url, params = params)
    info = response.json()
    return info

def pass_page_to_params(page):
    date_today_params = str(data_date.strftime("%d")+"."+data_date.strftime("%m")+"."+data_date.strftime("%Y"))
    date_tomorrow_params = str((data_date+timedelta(days = 1)).strftime("%d")+"."+(data_date+timedelta(days = 1)).strftime("%m")+"."+(data_date+timedelta(days = 1)).strftime("%Y"))

    params = {"sort_direction":"desc",
                "in":date_today_params,
                "out":date_tomorrow_params,
                "adults":"1",
                "page":page,
                "scenario":"desktop",
                "r":"0.5908996518525451"
                }
    return params

def write_to_file(data):
    with open("data_of_hotels.json","w", encoding="UTF-8") as file:
        json_data=json.dumps(data,ensure_ascii=False,indent=1)
        file.write(json_data) 

def get_count_pages():
    page = 0
    info = get_data_of_hotels(page)
    total = info["response"]["total"]
    count_pages = total // 21
    if total%21!=0:
        count_pages+=1
    return count_pages

def get_data_and_put_to_json():
    count_total = 0
    count_pages = get_count_pages()
    data_to_json_file = []

    try:
        connection = pymysql.connect(
            host = host,
            port = 3306,
            user = user,
            password = password,
            database = db_name,
            cursorclass = pymysql.cursors.DictCursor
        )
        print("Successfully connection")
        try:
            with connection.cursor() as cursor:
                check_db = f"use {db_name};"
                cursor.execute(check_db)
                print("Вы подключились к базе данных: ",db_name)

            with connection.cursor() as cursor:
                
                while count_pages!=0:
                    
                    page = count_pages
                    count_pages-=1
                    response = session.post(url = url, params = pass_page_to_params(page))
                    info = get_data_of_hotels(page)
                    count_total += info["response"]["count"]
                    
                    if response.status_code != 200:
                        print('error', page)
                        break
                    else:
                        info_json = response.json()
                        for i in info_json["response"]['hotels']:
                            data = {}
                            url_hotel = "https://101hotels.com/main/cities/"
                            name_hotel = ""

                            for j in i:
                                
                                if j =="id":
                                    id = i[j]
                                    data[id]={}
                            
                                if j=="full_name":
                                    name_hotel = i[j]
                                    data[id]["name"]=name_hotel
                                
                                if j =="address":
                                    address= i[j]
                                    data[id]["address"]=address

                                if j =="city_url":
                                    url_hotel=url_hotel+i[j]+"/"
                                if j =="url":
                                    url_hotel+=i[j]
                                    data[id]["url"]=url_hotel
                                    data[id]["resources"]="101hotels"
                                    resources="101hotels"
                                if j=="rooms":
                                    data[id]["rooms"]=[]
                                    for y in i[j]:
                                        data[id]["rooms"].append({"id_room":y["id"],"name_room":y["name"],"price":y["min_price"]})
                            
                            requests_put_data_hotel = f"INSERT INTO `hotels` (id_hotel,name_hotel,url_hotel,resourses,check_in,check_out) VALUES ({id},'{data[id]['name']}','{data[id]['url']}','{data[id]['resources']}','{date_today}','{date_tomorrow}');"
                            cursor.execute(requests_put_data_hotel)
                            connection.commit()

                            cursor.execute("SELECT `id` FROM hotels ORDER BY id DESC LIMIT 1;")
                            id_hotel = cursor.fetchone()
                            
                            for i in data[id]["rooms"]:
                                for elem in i:
                                    if elem =="id_room":
                                        id_room = i[elem]
                                    if elem =="name_room":
                                        name_room = i[elem]
                                    if elem =="price":
                                        price = i[elem]
                                requests_put_data_room = f"insert rooms(id_room,name_room,price,id_hotel) values({id_room},'{name_room}',{price},{id_hotel['id']});"
                                cursor.execute(requests_put_data_room)
                                connection.commit()
                            data_to_json_file.append(data)
        finally:
            connection.close()

    except Exception as ex:
        print("Сбой подключение по причине возникновения ошибки:")
        print(ex)
    try:            
        file = open("data_of_hotels.json","r")
        file = open("data_of_hotels.json","w",encoding="utf-8")
        json_data=json.dumps(data_to_json_file,ensure_ascii=False,indent=1)
        file.write(json_data)    
        print("Данные в файле data_of_hotels.json обновлены") 
    except:
        print("Файл data_of_hotels.json создан и заполнен данными")
        write_to_file(data_to_json_file)

def main():
    schedule.every().day.at("12:00").do(get_data_and_put_to_json)
    #schedule.every(15).seconds.do(get_data_and_put_to_json)
    while True:
        schedule.run_pending() 

if __name__ == "__main__":
    main()                    
