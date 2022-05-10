import scrapy
import json
import datetime


class DivarSpiderSpider(scrapy.Spider):
    name = 'divar_spider'

    @staticmethod
    def time_threshold():
        return datetime.date.today() - datetime.timedelta(days=30)

    @staticmethod
    def compare_date(epoch):
        return DivarSpiderSpider.time_threshold() < datetime.datetime.fromtimestamp(epoch/1000000.0).date()

    def start_requests(self):
        with open('districts.json', 'r') as f:
            districts = json.load(f)
            for district in districts:
                url = f'https://api.divar.ir/v8/web-search/tehran/buy-residential?districts={district}'
                yield scrapy.Request(
                    url=url, callback=self.parse, meta={'district_id': district})

    def parse(self, response):
        data = json.loads(response.body)
        district = response.meta.get('district')
        next_page = data.get('seo_details').get('next')
        last_post_date = data.get('last_post_date')
        homes = data.get("widget_list")
        if DivarSpiderSpider.compare_date(last_post_date):
            for home in homes:
                token = home.get('data').get('token')
                return scrapy.Request(
                    url=f'https://api.divar.ir/v5/posts/{token}', callback=self.parse_post, meta={'district_id': district})
            if next_page:
                url = f"https://api.divar.ir/v8/web-search/{next_page}"
                yield scrapy.Request(url=url, callback=self.parse)

    def parse_post(self, response):
        result = {'district_id': None, 'business_type': None,
                  'city_fa': None, 'category': None, 'token': None,
                  'city_en': None, 'business_type': None, 'business_ref': None,
                  'price': None, 'district': None, 'area': None, 'year': None,
                  'room': None, 'total_price': None, 'meter_price': None, 'floor': None,
                  'elevator': None, 'parking': None, 'warehouse': None, 'unit_count_floor': None,
                  'contract': None, 'building_direction': None, 'elevator': None, 'parking': None,
                  'warehouse': None, 'balcony': None, 'ceramic_floor': None, 'wc': None,
                  'split_cooler': None, 'split_heater': None, 'package': None, 'lat': None,
                  'long': None, 'img_0': None, 'img_1': None, 'img_2': None, 'img_3': None,
                  'img_4': None, 'img_5': None, 'img_6': None, 'img_7': None, 'img_8': None,
                  'img_9': None}
        detail = json.loads(response.body)
        result['district_id'] = response.meta.get('district')
        data = detail.get('data')
        result['business_type'] = data['business_data']['business_type']
        result['city_fa'] = data.get('city')
        webengage = data.get('webengage')
        result['category'] = webengage.get('category')
        result['token'] = webengage.get('token')
        result['city_en'] = webengage.get('city')
        result['business_type'] = webengage.get('business_type')
        result['business_ref'] = webengage.get('business_ref')
        result['price'] = webengage.get('price')
        result['district'] = data.get('district')
        widgets = detail.get('widgets')
        more_info = widgets.get('list_data')
        first_info = more_info[0]
        item_one = first_info.get('items') # this returns none some times
        result['area'] = item_one[0].get('value')
        result['year'] = item_one[1].get('value')
        result['room'] = item_one[2].get('value')
        result['total_price'] = more_info[1].get('value')
        result['meter_price'] = more_info[2].get('value')
        result['floor'] = more_info[4].get('value')
        features = more_info[5].get('items')
        result['elevator'] = features[0].get('available')
        result['parking'] = features[1].get('available')
        result['warehouse'] = features[2].get('available')
        next_page = more_info[5].get('next_page')
        if next_page:
            widget_list = next_page.get('widget_list')
            result['unit_count_floor'] = widget_list[1].get('value')
            result['contract'] = widget_list[2].get('value')
            result['building_direction'] = widget_list[3].get('value')
            result['elevator'] = widget_list[5].get('value')
            result['parking'] = widget_list[6].get('value')
            result['warehouse'] = widget_list[7].get('value')
            result['balcony'] = widget_list[8].get('value')
            result['ceramic_floor'] = widget_list[9].get('value')
            result['wc'] = widget_list[10].get('value')
            result['split_cooler'] = widget_list[11].get('value')
            result['split_heater'] = widget_list[12].get('value')
            result['package'] = widget_list[12].get('value')
        location = widgets.get('location')
        if location:
            result['lat'] = location.get('latitude')
            result['long'] = location.get('longitude')
        images = location = widgets.get('images')
        if images:
            for img in range(len(images)):
                try:
                    result[f'img_{img}'] = images[img]
                except:
                    pass    
        yield result
