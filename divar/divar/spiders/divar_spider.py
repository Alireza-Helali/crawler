import scrapy
import json
import datetime


class DivarSpiderSpider(scrapy.Spider):
    name = 'divar_spider'

    @staticmethod
    def time_threshold():
        return datetime.date.today() - datetime.timedelta(days=5)

    @staticmethod
    def compare_date(epoch):
        return DivarSpiderSpider.time_threshold() < datetime.datetime.fromtimestamp(epoch/1000000.0).date()

    def start_requests(self):
        with open('districts.json', 'r') as f:
            districts = json.load(f)
            for district in districts:
                url = f'https://api.divar.ir/v8/web-search/tehran/buy-apartment?districts={district}'
                yield scrapy.Request(
                    url=url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body)
        next_page = data.get('seo_details').get('next')
        last_post_date = data.get('last_post_date')
        homes = data.get("widget_list")
        if DivarSpiderSpider.compare_date(last_post_date):
            for home in homes:
                token = home.get('data').get('token')
                yield scrapy.Request(
                    url=f'https://api.divar.ir/v5/posts/{token}', callback=self.parse_post)
            if next_page:
                url = f"https://api.divar.ir/v8/web-search/{next_page}"
                yield scrapy.Request(url=url, callback=self.parse)
        
    def parse_post(self, response):
        result = {}
        detail = json.loads(response.body)
        data = detail.get('data')
        result['business_type'] = data['business_data']['business_type']
        webengage = data.get('webengage')
        result['price'] = webengage.get('price')
        result['district'] = data.get('district')
        widgets = detail.get('widgets')
        more_info = widgets.get('list_data')
        for data in more_info:
            format = data.get('format')
            if format == 'group_info_row':
                items = data.get('items')
                for item in items:
                    result[item.get('title')] = item.get('value')
            elif format == 'string':
                result[data.get('title')] = data.get('value')
            elif format == 'group_feature_row':
                items = data.get('items')
                for item in items:
                    result[item.get('title')] = item.get('available')
                next_page = data.get('next_page')
                if next_page:
                    widget_list = next_page.get('widget_list')
                    for feature in widget_list:
                        feature_data = feature.get('data')
                        widget_type = feature.get('widget_type')
                        if widget_type == "UNEXPANDABLE_ROW":
                            result[feature_data.get(
                                'title')] = feature_data.get('value')
                        elif widget_type == "FEATURE_ROW":
                            icon = feature_data.get('icon')
                            result[icon.get('icon_name')
                                   ] = feature_data.get('title')
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
