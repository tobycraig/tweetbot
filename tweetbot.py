import html
import time
import twitter
import unidecode

# tweet display settings
SCREEN_NAME = 'metaltoad'   # the Twitter account to retrieve tweets from
DELAY = 3                   # how long in seconds to pause between pages
NUM_TWEETS = 10             # how many of the latest tweets to cycle through

# LCD screen settings
COLUMNS = 20                # number of columns the screen has
LINES = 4                   # number of lines the screen has
I2C = True                  # whether to use I2C or GPIO
# I2C settings; not needed if using GPIO
PORT_EXPANDER = 'PCF8574'   # PCF8574, MCP23008 or MCP23017, found on chip
I2C_ADDRESS = 0x27          # found using `sudo i2cdetect -y 1`
# GPIO pin numbers; not needed if using I2C
PIN_RS = 36
PIN_E = 18
PINS_DATA = [16, 11, 40, 15]

# set up connection to Twitter API
api = twitter.Api(consumer_key='YOUR CONSUMER KEY',
                  consumer_secret='YOUR CONSUMER SECRET',
                  access_token_key='YOUR ACCESS TOKEN KEY',
                  access_token_secret='YOUR ACCESS TOKEN SECRET',
                  tweet_mode='extended') # get full tweet text rather than an abbreviated version

# set up LCD screen according to settings
if I2C:
    from RPLCD.i2c import CharLCD
    lcd = CharLCD(PORT_EXPANDER, I2C_ADDRESS)
else:
    import RPi.GPIO as GPIO
    from RPLCD import CharLCD
    lcd = CharLCD(cols=COLUMNS, rows=LINES, pin_rs=PIN_RS, pin_e=PIN_E, pins_data=PINS_DATA)

# main loop
def main():
    while True:
        try:
            # fetch latest tweets and process them
            latest_tweets = get_tweets()
            # display them on the LCD screen
            print_tweets(latest_tweets)
        except:
            # in case of an error (eg network failure or Twitter unavailability), wait for a minute then try again
            time.sleep(60)

def get_tweets():
    # output status message
    lcd_print('Tweetbot\r\nRefreshing...')

    # get data from Twitter. include_rts=False prevents retweets from being included
    statuses = api.GetUserTimeline(screen_name=SCREEN_NAME, include_rts=False)

    # process the most recent NUM_TWEETS tweets we received
    tweets = []
    for tweet in statuses[:NUM_TWEETS]:
        # each tweet will be converted into one or more lines to be displayed on the screen
        lines = []

        # clean up text
        text = html.unescape(tweet.full_text)
        text = unidecode.unidecode(text)

        # get list of words in tweet
        words = []
        for word in text.split():
            while len(word) > COLUMNS:
                # word is too long for the screen, chop it up
                words.append(word[:COLUMNS])
                word = word[COLUMNS:]
            words.append(word)

        # distribute list of words across as many lines as are needed
        # track where the last break occurred
        last_break = 0
        # track how much space is left in this line
        remainder = COLUMNS
        for i, w in enumerate(words):
            if len(w) > remainder:
                # adding this word would go over the boundary
                # add the words so far to a new line
                lines.append(' '.join(words[last_break:i]))
                # and note where this break took place
                last_break = i
                # reset the amount of space remaining for the next line
                remainder = COLUMNS
            # reduce the amount of space remaining to account for this word and a space
            remainder = remainder - (len(w) + 1)
        # add the remainder of the tweet
        lines.append(' '.join(words[last_break:]))
        # finished preparing this tweet, add it to the list
        tweets.append(lines)
    return tweets

def print_tweets(tweets):
    for tweet in tweets:
        # go through the tweet, printing enough lines at a time to fill the screen
        for i in range(0, len(tweet), LINES):
            # display this page of the tweet on the LCD
            lcd_print('\r\n'.join(tweet[i:i+LINES]))
        # output stars between tweets
        lcd_print('* ' * (COLUMNS // 2))

def lcd_print(content):
    # clear LCD screen
    lcd.clear()
    # write the content
    lcd.write_string(content)
    # wait for a sec
    time.sleep(DELAY)

if __name__ == '__main__':
    try:
        # start the main loop
        main()
    finally:
        if not I2C:
            # clean up GPIO if necessary
            GPIO.cleanup()
