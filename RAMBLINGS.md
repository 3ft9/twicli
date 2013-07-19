Ramblings
=========

My motivation for writing TwiCLI has come from my frustration with the Twitter clients that are out there, and Twitter's "guidelines" on how tweets should be displayed. I find it incredibly clunky and inefficient, but they set the rules which is why this will never be an actual product.

Todo
----

At this early stage there are specific things that need to be done before anything else. Once the basic structure is solid and the essential UI parts are implemented this todo list will be expanded to include everything else.

* Reorganise code so the UI and streaming are separate, with the streaming happening in a thread and passing data to a callback on the UI thread.
* Implement the input box in the UI.

How will it work?
-----------------

It's written in Python and uses [Twython](https://github.com/ryanmcgrath/twython) to talk to Twitter. I went back and forth about how to do the UI but eventually decided upon Curses as it does everything I'll want, and the Python binding isn't too bad.

The UI will be pretty similar to the de facto standard for IRC - input box at the bottom, tweets and other messages above that to the top. Left column for the message source, and the actual message on the right. Muted colours will be used to visually separate out the different areas, and I'm hoping to avoid having lines all over the screen.

Tweet buffer
------------

The message window will have two modes: live and buffered. In live mode messages will be displayed as soon as they are received. In buffered mode they will be buffered until the user requests them. In buffered mode they will be able to request any number of messages to be displayed as well as simply 'the next screens-worth'.

Clearly there will need to be an indication of the buffer size somewhere on the screen.

There will also need to be a (configurable) maximum number of tweets that will be held in the buffer.

Commands
--------

Commands will be similar to IRC. Anything typed in the input box that doesn't start with a / will be tweeted when the enter key is hit.

The full list of commands will grow as it's developed, but the following will be the first to be supported:

* /v num

Show the next num tweets in the buffer. If num is ommitted it will show the next tweet.

* /p

Show the next page of tweets. This will need to calculate how many of the buffered tweets can be shown before they go off the top of the screen.

* /r id ...

Reply to the specified tweet. Tweets are referenced by numbers that will appear on the UI. They will be between 00 and 99, and will be required to have two digits to help limit potential typos.

This will be implemented using an array and a current_position index into it. Each item in the array will be the unchanged message object received so commands will have full access to the tweet/whatever.

Ideally, when you type the space after the ID it will automatically add the @screen_name. The user is then free to remove it and it will still be sent as a reply to that tweet.

* /rt id

Retweet the specified tweet. This will send a standard Twitter retweet.

* /rte id

This will replace the input line with the specified tweet text so the user can edit it before retweeting.

* /delete

Delete the last tweet sent. My initial thought was that this would only work on the last tweet but it may be worth storing a stack of tweets sent so this command can be issued multiple times (configurable, default 100?). Only the tweet ID and text need to be stored so we can actually delete it and show the user what they deleted in case they made a mistake.

* /follow screen_name

Start following @screen_name.

* /unfollow screen_name

Stop following @screen_name.

* /quit

Exit from TwiCLI.
