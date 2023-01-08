import snscrape.modules.twitter as twitterScraper
import json
import pandas as pd
import colorama
from unidecode import unidecode

colorama.init()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
class scraper:
    def twitterUser():
        choose1 = str(input(bcolors.BOLD + bcolors.OKBLUE + "Enter the username, without the @ sign and without spaces:" + bcolors.ENDC))
        while not choose1.strip():
            choose1 = str(input(bcolors.BOLD + bcolors.OKBLUE + "Enter the username, without the @ sign and without spaces:" + bcolors.ENDC))
        choose2 = choose1.replace(" ", "")
        choose = unidecode(choose2, "utf-8")

        scraper = twitterScraper.TwitterUserScraper(choose, False)

        while True:
            try:
                m = int(input(bcolors.BOLD + bcolors.OKBLUE + "Enter how many tweets to display:" + bcolors.ENDC))
                n = int(m)
                if n > 0:
                    break
                else:
                    print(
                        bcolors.BOLD + bcolors.FAIL + "\n The digit must be greater than 0\n" + bcolors.ENDC)
                    continue
            except ValueError:
                print(bcolors.BOLD + bcolors.WARNING + "\n You need to enter a number, please try again \n" + bcolors.ENDC)
                continue
        tweets = []

        for i, tweet in enumerate(scraper.get_items()):
            if i > n:
                break
            print(f"{i} content: {tweet.content}, data: {tweet.date}")
            tweets.append({"id": tweet.id, "content": tweet.content, "media": str(tweet.media),
                           "user": tweet.user.username, "user_location": tweet.user.location,
                           "url": tweet.url, "likes": tweet.likeCount})

        f = open("results/tweets_user.json", "w")
        j = json.dumps(tweets)
        f.write(j)
        f.close()
        # path = Path(r'tweets.json')
        with open('results/tweets_user.json', 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        df = pd.json_normalize(data)
        df.to_csv('results/tweets_user.csv', index=False, encoding='utf-8')
        print(
            bcolors.BOLD + bcolors.WARNING + "\nThe results were saved to the results folder in the tweets_search.json and tweet_search.csv files" + bcolors.ENDC)


    def twitterSearch():
        choose = str(input(bcolors.BOLD + bcolors.OKGREEN + "Enter search data: " + bcolors.ENDC))
        while not choose.strip():
            choose = str(input(bcolors.BOLD + bcolors.OKGREEN + "Enter search data: ` " + bcolors.ENDC))
        scraper = twitterScraper.TwitterSearchScraper(choose, False)

        while True:
            try:
                m = int(input(bcolors.BOLD + bcolors.OKBLUE + "Enter how many tweets to display: " + bcolors.ENDC))
                n = int(m)
                if n > 0:
                    break
                else:
                    print(
                        bcolors.BOLD + bcolors.FAIL + "\n The digit must be greater than 0\n" + bcolors.ENDC)
                    continue
            except ValueError:
                print(bcolors.BOLD + bcolors.WARNING + "\n You need to enter a number, please try again \n" + bcolors.ENDC)
                continue
        tweets = []

        for i, tweet in enumerate(scraper.get_items()):
            if i > n:
                break
            print(f"{i} content: {tweet.content}, user: {tweet.user.username}, data: {tweet.date}")
            tweets.append({"id": tweet.id, "content": tweet.content, "data": str(tweet.date), "user": tweet.user.username,
                           "user_location": tweet.user.location, "url": tweet.url, "media": str(tweet.media), "likes": tweet.likeCount})

        f = open("results/tweets_search.json", "w")
        j = json.dumps(tweets)
        f.write(j)
        f.close()
        # path = Path(r'tweets.json')
        with open('results/tweets_search.json', 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        df = pd.json_normalize(data)
        df.to_csv('results/tweets_search.csv', index=False, encoding='utf-8')
        print(
            bcolors.BOLD + bcolors.WARNING + "\nThe results were saved to the results folder in the tweets_search.json and tweet_search.csv files\n" + bcolors.ENDC)