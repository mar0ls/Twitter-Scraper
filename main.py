import colorama
from sys import exit
from engine import bcolors, scrapeer

colorama.init()




print(bcolors.OKGREEN + bcolors.BOLD + '''_|_|_|_|_|  _|          _|  _|_|_|  _|_|_|_|_|  _|_|_|_|_|  _|_|_|_|  _|_|_|    _|_|_|_|  _|    _|  
    _|      _|          _|    _|        _|          _|      _|        _|    _|  _|        _|  _|    
    _|      _|    _|    _|    _|        _|          _|      _|_|_|    _|_|_|    _|_|_|    _|_|      
    _|        _|  _|  _|      _|        _|          _|      _|        _|    _|  _|        _|  _|    
    _|          _|  _|      _|_|_|      _|          _|      _|_|_|_|  _|    _|  _|_|_|_|  _|    _|  

---------------------------m4r0ls------------------                                 
           ''' + bcolors.ENDC)
print(bcolors.OKBLUE + bcolors.BOLD + "M E N U" + bcolors.ENDC)
menu_options = {
    1: bcolors.BOLD + 'start tweet search',
    2: 'start a search using the tweet search engine of a specific user',
    3: 'to display help',
    4: 'to end the program' + bcolors.ENDC,
}


def print_menu():
    for key in menu_options.keys():
        print(key, '[*]', menu_options[key])


def option1():
    scrapeer.twitterSearch()


def option2():
    scrapeer.twitterUser()


def option3():
    print('''[*] If you chose option 1 then you can search for example:

   [+] Tweet search.
        Enter the content of the origin in the added tweets. Then indicate the number of records they have
        look.

   [+] When searching for tweets, you can use operators like
        '-' - excluded word
        '# or $' - hashtags for all searches or cashtag for stock searches
        'lang:pl' - find teets in Polish
        'from:user' - tweets sent by an efficient user, e.g. from:PaniNowakowa or dogs from:Nasa
        'to:user' - responds to tweet queries similar to option 2
        '@user' mentions a specific @user
        'list:715919216927322112' Tweets from this public list. Use list id from API or with urls,
                                         like twitter.com/i/lists/715919216927322112.
        'filter:verified' - tweets from verified users
        'filter:blue_verified' tweets from 'verified' users who paid $8 for Twitter Blue 

   [+] When searching where time is important, you can enter the data to be searched with:
        'science:2022-12-31' - on or after (inclusive) the specified date. 4-digit year, 2-digit month, 2-digit day separated by a hyphen.
        'until:2022-12-31' - before (NOT including) the specified date. Combine with the "from" operator for dates between.
   [+] When searching geo, you can enter the data to search along with:
        'near:city' - geotagged here, e.g. near:Warsaw
        'geocode:lat,long,radius' - get tweets 10km around Twitter HQ, use geocode:37.7764685,-122.4172004,10km
        'place:96683cc9126741d1' - search for tweets by object ID, e.g.: USA Place ID is96683cc9126741d1

	 For example, let's say you want to find all pizza tweets in Los Angeles
               at a distance of 10 km.
        This can be achieved with the following command:
        pizza near:"Los Angeles" within:10km
        OR
               34.052235, -118.243683, 10km

        REMEMBER!!
        There are two ways to get your location from Twitter; geotag from a specific tweet
        or a user's location as part of their profile. According to Twitter, only 1-2% of tweets
        it's geographically tagged, so it's not a good indicator; significant on the other hand
        number of users have location in their profile but can type whatever they want. Some
        they are nice to people like us and will write "London, England" or something similar while
        others are less helpful, putting things like "My parents' basement".

[*] If you chose option 2, you can search for example:

   [+] Search for user's tweets.
Enter a username. Then indicate the number of records they have
be returned.

[*] More about advanced search on tweeter https://github.com/igorbrigadir/twitter-advanced-search
''')


if __name__ == '__main__':
    while (True):
        print_menu()
        option = ''
        try:
            option = int(input(bcolors.BOLD + 'Your choise: ' + bcolors.ENDC))
        except:
            print(bcolors.FAIL + 'Try again by entering a number ☻☻☻' + bcolors.ENDC)

        if option == 1:
            option1()
        elif option == 2:
            option2()
        elif option == 3:
            option3()
        elif option == 4:
            print('Have a nice day ☻')
            exit()
        else:
            print(bcolors.FAIL + 'You have made a selection that does not match the menu. Please enter a number from 1 to 4.' + bcolors.ENDC)