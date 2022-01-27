from chalice import Chalice
from chalicelib import ESPNScraper

app = Chalice(app_name='sport-api')


@app.route('/')
def index():
    return {'message': 'server up and running!'}


@app.route('/{sport}', methods=['GET'])
def api_schedule(sport):
    data = ESPNScraper(sport=sport)
    return data.getData()


@app.route('/{sport}/{date}', methods=['GET'])
def api_schedule_date(sport, date):
    data = ESPNScraper(sport=sport, date=date)
    return data.getData()



