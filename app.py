import sqlalchemy as db
import requests
from sqlalchemy.engine.base import Connection


def databse_connection() -> Connection:
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'python_app',
        'password': 'my_python_password',
        'database': 'crypto'
    }


    db_user = config.get('user')
    db_pwd = config.get('password')
    db_host = config.get('host')
    db_port = config.get('port')
    db_name = config.get('database')
    connection_str = f'mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}'
    engine = db.create_engine(connection_str)
    connection =  engine.connect()
    return connection


def get_bitcoin_rate() -> float:
    try:
        res = requests.get('https://rest.coinapi.io/v1/exchangerate/BTC/USD', headers={'X-CoinAPI-Key' : api_key}).json()
        # print(json.dumps(res, indent=4))
        rate = res['rate']
        return rate
    except Exception as e:
        print(e)
        return None

def get_raw_data() -> dict:
    db_data = connection.execute('select max(iteration_id),sum(current_rate),max(current_rate), min(current_rate) from bitcoin_rates').fetchone()
    return {'num_iterations':db_data[0], 'current_sum' : db_data[1],'max_rate' :db_data[2], 'min_rate' : db_data[3]}

def calculate_new_avarage(divider:int, rates_sum:float) -> float:
    return rates_sum / divider

def _insert_into_db(current_rate, avarage_rate) -> None:
    connection.execute(f'insert into bitcoin_rates (current_rate,avarage_rate) values({current_rate}, {avarage_rate})')

def _print(max_rate:float, min_rate:float, avarage_rate:float, recommendation:bool) -> None:
    print('Max Rate:',max_rate)
    print('Min Rate:',min_rate)
    print('Avg Rate:', avarage_rate)
    print('Should You Buy?', recommendation)

def get_last_5_rows_avg() -> float:
    return connection.execute('select avg(current_rate) from ( select * from bitcoin_rates order by iteration_id desc limit 5) last5_rows_query order by iteration_id;').fetchone()[0]

# def calculate_rates_slope(rates_list: list) -> float:
#     slope, intercept, r_value, p_value, std_err = linregress(list(range(len(rates_list))),rates_list)
#     return slope

def should_buy(current_rate:float, last5_min_avg:float) -> bool:
    return current_rate < last5_min_avg

def _close_db_connection() -> None:
    connection.close()
    



if __name__ == '__main__':
    connection = databse_connection()
    api_key = '9BBE3B6F-3D3D-43D7-9A6D-C29878875DCE'
    current_bit_rate = get_bitcoin_rate()
    print(current_bit_rate)
    current_db_data = get_raw_data()
    new_avarage = calculate_new_avarage(current_db_data['num_iterations'] + 1, current_db_data['current_sum'] + current_bit_rate)
    max_rate = current_bit_rate if current_bit_rate > current_db_data['max_rate'] else current_db_data['max_rate']
    min_rate = current_bit_rate if current_bit_rate < current_db_data['min_rate'] else current_db_data['min_rate']
    last_5_rows_avg = get_last_5_rows_avg()
    _insert_into_db(current_bit_rate, new_avarage)
    recommendation = should_buy(current_bit_rate, last_5_rows_avg)
    _print(max_rate, min_rate, new_avarage, recommendation)
    _close_db_connection()