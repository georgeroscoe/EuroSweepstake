import requests
import pandas as pd
import regex as re
from bs4 import BeautifulSoup


def scrape_url(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup


squads = ['Austria', 'Belgium', 'Croatia', 'Czech Republic', 'Denmark', 'England', 'Finland', 'France', 'Germany',
          'Hungary', 'Italy', 'Netherlands', 'North Macedonia', 'Poland', 'Portugal', 'Russia', 'Scotland',
          'Slovakia', 'Spain', 'Sweden', 'Switzerland', 'Turkey', 'Ukraine', 'Wales']


def combine_stats_and_discipline(stats_df, discipline_df):
    complete_df = stats_df.join(discipline_df, how='left')
    complete_df.sort_values(by='xGD per 90', ascending=False, inplace=True)
    complete_df.to_csv('sweepstake_scores.csv')
    return complete_df


def get_squad_standard_stats(parsed_url):
    squad_dict = {}
    for squad in squads:
        squad_dict[squad] = {'xG per 90': '', 'xGA per 90': ''}

    all_tables = parsed_url.findAll("tbody")
    squad_stats = all_tables[0]
    opponent_stats = all_tables[1]
    both_stats = [squad_stats, opponent_stats]

    for stat_list in both_stats:

        rows = stat_list.find_all('tr')

        for row in rows:

            if row.find('th', {"scope": "row"}) is not None:
                squad = row.find("th", {"data-stat": "squad"}).text.strip()
                squad_text = squad[squad.find(' ') + 1:] if stat_list == squad_stats else squad[squad.find(' ') + 4:]
                xg = row.find("td", {"data-stat": 'xg_per90'})
                a = xg.text.strip().encode()
                xg_text = a.decode("utf-8")
                if stat_list == squad_stats:
                    squad_dict[squad_text]['xG per 90'] = float(xg_text)
                else:
                    squad_dict[squad_text]['xGA per 90'] = float(xg_text)

    squad_df = pd.DataFrame.from_dict(squad_dict).transpose()
    squad_df['xGD per 90'] = squad_df['xG per 90'] - squad_df['xGA per 90']

    return squad_df.round(2)


def get_disciplinary_stats(parsed_url):
    squad_dict = {}
    for squad in squads:
        squad_dict[squad] = {'Yellow Cards': '', 'Straight Red Cards': ''}
    all_tables = parsed_url.findAll("tbody")
    squad_stats = all_tables[0]
    rows = squad_stats.find_all('tr')
    for row in rows:

        if row.find('th', {"scope": "row"}) is not None:
            squad = row.find("th", {"data-stat": "squad"}).text.strip()
            squad_text = squad[squad.find(' ') + 1:]
            red_card = row.find("td", {"data-stat": 'cards_red'})
            second_yellow_card = row.find("td", {"data-stat": 'cards_yellow_red'})
            yellow_card = row.find("td", {"data-stat": 'cards_yellow'})
            a = red_card.text.strip().encode()
            b = second_yellow_card.text.strip().encode()
            c = yellow_card.text.strip().encode()
            red_cards = int(a.decode("utf-8"))
            second_yellow_cards = int(b.decode("utf-8"))
            yellow_cards = int(c.decode("utf-8"))

            squad_dict[squad_text]['Straight Red Cards'] = red_cards - second_yellow_cards
            squad_dict[squad_text]['Yellow Cards'] = yellow_cards

    squad_df = pd.DataFrame.from_dict(squad_dict).transpose()

    # 1 point for a yellow card, 3 points for a straight red card
    squad_df['Card Points'] = squad_df['Yellow Cards'] + 3 * squad_df['Straight Red Cards']
    return squad_df


if __name__ == '__main__':
    squad_page = scrape_url('https://fbref.com/en/comps/676/stats/UEFA-Euro-Stats')
    disciplinary_page = scrape_url('https://fbref.com/en/comps/676/misc/UEFA-Euro-Stats')
    euro_page = scrape_url('https://fbref.com/en/comps/676/UEFA-Euro-Stats')

    squad_standard_stats_df = get_squad_standard_stats(squad_page)
    squad_disciplinary_df = get_disciplinary_stats(disciplinary_page)

    stats_and_discipline = combine_stats_and_discipline(squad_standard_stats_df, squad_disciplinary_df)
