# CATCHAT
### Video Demo: https://youtu.be/RmPbx0DUP3A?si=8Q-2BYwNqwZW23mT

## Description:
Cat Chat is a real-time cat-themed chat web application that consists of several features like individual chats, group chats, mood selectors, etc., with a humorous touch of funny cat memes. A user can also modify his or her profile and delete his or her account. It is programmed by front-end __HTML, CSS, Javascript__ and back-end __flask web sockets, Python, and SQL__.

### Screenshots:
<img src="https://github.com/i1amaj/Catchat/assets/146009506/4c3d75b3-5dc1-40fe-bab5-6d570c3410e6" alt="Chat"/>
<img src="https://github.com/i1amaj/Catchat/assets/146009506/3fbc4e8c-ed6f-4cd3-9de5-7317581adbdc" alt="Froup"/>
<img src="https://github.com/i1amaj/Catchat/assets/146009506/19285afc-c76d-43ca-865f-1ee6930c661e" alt="Status" />
<img src="https://github.com/i1amaj/Catchat/assets/146009506/3961c600-6595-4706-a5ae-97ccb9c5151d" alt="Mood" />

## Details:
It consists of the following parts:

### Register:
This allows users to register a new account. It also ensures that the registered user has a unique name and unique user ID.

### Login:
This allows the user to log in and then create flask sessions for the current user.

### Chat
This allows users to chat in real-time using Flask web sockets. It also stores the user chats in a SQL database. The users can chat individually as well as in a group.

### Group chat:
This allows users to chat in a group. This generates a 4-digit unique code for each group, and the user can join the group using this unique code.

### Mood:
This allows users to select a funny cat meme according to their mood for the day. There are 35 different moods a user can choose from.

### Status:
This displays the moods of the user and his or her friends. Also, it displays the most used mood as the mood of the day.

### Profile:
The user can also modify his or her profile.  The user can change his or her profile picture by providing a valid URL, can change the current password, and can also delete the account, which in turn deletes user messages and other belongings.

## Files and Folders:

### static:
It contains the CSS code to make the site visually pleasing.

### templates
It contains the HTML files along with the related Javascript code to establish sockets and other functionalities. There are 7 HTML files, each related to the related functionality.

### app.py
The main backend file consists of Flask web sockets to allow real-time chatting, storing and altering data in the SQL database, and establishing connections between clients. It is mainly programmed with Flask and Python and connected to the front-end HTML using Jinja.

### catchat.db
It is the SQL database in which data is stored and organized.
