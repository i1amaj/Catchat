import sqlite3
from flask import Flask, redirect, render_template, request, session
import socketio
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import join_room, leave_room, send, SocketIO
from datetime import datetime
import random

app = Flask(__name__)
socketio = SocketIO(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "secretissecret!"

# creating connection
conn = sqlite3.connect("catchat.db", check_same_thread=False)
db = conn.cursor()


@app.route("/")
def main():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        # naming input variables
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # checking whether the password match or not
        if password != confirmation:
            error = "Password doesn't match!"
            return render_template("register.html", error=error)

        elif username:
            result = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchall()
            if result:
                error = "Username taken!"
                return render_template("register.html", error=error)

            elif "-" in username:
                error = "Username should not contain dashes!"
                return render_template("register.html", error=error)

            else:
                # encrypting the passcode
                hash = generate_password_hash(password)

                # updating users table
                db.execute(
                    "INSERT INTO users (username, hash) VALUES(?,?)", (username, hash)
                )
                conn.commit()

                return redirect("/login")

    error = ""
    return render_template("register.html", error=error)


@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # checking the user username and password
        if username and password:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchall()

            # if not throws errors
            if not user or not check_password_hash(user[0][2], password):
                error = "Invalid username and/or password!"
                return render_template("login.html", error=error)

            # if yes create sessions
            session["username"] = user[0][1]
            session["name"] = user[0][3]
            session["image"] = user[0][3]
            session["mood"] = user[0][4]

            return redirect("/home")

    error = ""
    return render_template("login.html", error=error)


@app.route("/home", methods=["POST", "GET"])
def home():
    # displaying friends in friends list
    already_friends = []
    already_friends_name = []

    # extrating friend from friends list
    already_friends_dic = db.execute(
        "SELECT friend FROM friends WHERE username = ?", (session.get("username"),)
    ).fetchall()

    # storing them in a list
    for friend in already_friends_dic:
        friends_image = db.execute(
            "SELECT image FROM users WHERE username = ?", (friend[0],)
        )
        for friend_image in friends_image:
            already_friend = {
                "name": friend[0],
                "image": friend_image[0],
            }
            already_friends_name.append(friend[0])
            already_friends.append(already_friend)

    # if request method is post
    if request.method == "POST":
        username = session.get("username")
        search = request.form.get("search")

        # finding and displaying the users after searching
        friends = []
        friends_dic = db.execute(
            "SELECT username,image FROM users WHERE username LIKE ?",
            ("%" + search + "%",),
        )
        for friend in friends_dic:
            if friend[0] != username and friend[0] not in already_friends_name:
                friend = {"name": friend[0], "image": friend[1]}
                friends.append(friend)

        return render_template(
            "chat.html",
            friends=friends,
            friends_dic=friends_dic,
            already_friends=already_friends,
        )

    return render_template("chat.html", already_friends=already_friends)


@app.route("/chat", methods=["POST", "GET"])
def chat():
    # creating and checking the code session
    username = session.get("username")
    friend = request.form.get("friend")

    # checking if the other user has already connected with you
    code = friend + "-" + username

    contacts = db.execute("SELECT * FROM contacts WHERE code = ?", (code,)).fetchall()
    if contacts:
        session["room"] = code

    # if user has not contacted
    elif not contacts:
        # if the user has contacted itself
        new_code = username + "-" + friend
        contacted = db.execute(
            "SELECT * FROM contacts WHERE code = ?", (new_code,)
        ).fetchall()

        # if no one has contacted
        if not contacted:
            db.execute("INSERT INTO contacts(code) VALUES(?)", (new_code,))
            db.execute(
                "INSERT INTO friends(username,friend) VALUES(?,?)",
                (
                    username,
                    friend,
                ),
            )
            db.execute(
                "INSERT INTO friends(username,friend) VALUES(?,?)",
                (
                    friend,
                    username,
                ),
            )
            print("okay!")
            conn.commit()

        session["room"] = new_code

    # displaying old messages
    chats = []
    chat_dic = db.execute("SELECT * FROM messages WHERE code = ?", (session["room"],))

    for messages in chat_dic:
        chatings = {
            "username": messages[1],
            "message": messages[2],
            "time": messages[3],
            "image": messages[4],
        }
        chats.append(chatings)

    # displaying dp of friend
    friend_data = []
    friend_dic = db.execute(
        "SELECT username, image FROM users WHERE username = ?", (friend,)
    ).fetchall()
    for friend in friend_dic:
        friend = {"username": friend[0], "image": friend[1]}
        friend_data.append(friend)

    # displaying friends in friends list
    already_friends = []
    already_friends_name = []
    already_friends_dic = db.execute(
        "SELECT friend FROM friends WHERE username = ?", (session.get("username"),)
    ).fetchall()

    # saving them in a list
    for friend in already_friends_dic:
        friends_image = db.execute(
            "SELECT image FROM users WHERE username = ?", (friend[0],)
        )
        for friend_image in friends_image:
            already_friend = {
                "name": friend[0],
                "image": friend_image[0],
            }
            already_friends_name.append(friend[0])
            already_friends.append(already_friend)

        
    return render_template(
        "chat.html",
        friend=friend,
        friend_data=friend_data,
        chats=chats,
        username=username,
        already_friends=already_friends,
    )


@app.route("/group", methods=["POST", "GET"])
def group():
    # displaying old groups
    user_groups = []
    user_groups_dic = db.execute(
        "SELECT code FROM groups WHERE member = ?" , (session.get("username"),)
    ).fetchall()

    for group in user_groups_dic:
        user_groups.append(group[0])

    if request.method == "POST":
        code = request.form.get("group_code")
        username = session.get("username")

        group_codes = db.execute(
            "SELECT code FROM groups WHERE code = ?", (code,)
        ).fetchall()
        if not group_codes:
            error = "Invalid group code!"
            return render_template("group.html", error=error,user_groups=user_groups)
        else:
            group_members = db.execute("SELECT member FROM groups WHERE code = ?", (code,)).fetchall()
            # if user is already not a member of group and the current group is not in user groups
            if username not in group_members and code not in user_groups:
                db.execute("INSERT INTO groups(code,member) VALUES(?,?)", (code, username,))
                conn.commit()
            session["room"] = code
            return redirect("/groupchat")

    return render_template("group.html", user_groups=user_groups)


@app.route("/create_group", methods=["POST", "GET"])
def create_group():

    # displaying old groups
    user_groups = []
    user_groups_dic = db.execute(
        "SELECT code FROM groups WHERE member = ?" , (session.get("username"),)
    ).fetchall()

    for group in user_groups_dic:
        user_groups.append(group[0])

    if request.method == "POST":
        # creating new 4 digit code for each group
        code_list = []
        while True:
            for i in range(4):
                code_list.append(str(random.randint(0, 9)))

            code = "".join(code_list)

            group_codes = db.execute(
                "SELECT code FROM groups WHERE code = ?", (code,)
            ).fetchall()
            if not group_codes:
                db.execute("INSERT INTO groups(code) VALUES(?)", (code,))
                conn.commit()
                break

        return render_template("group.html", code=code,user_groups=user_groups)

    return render_template("group.html",user_groups=user_groups)


@app.route("/groupchat", methods=["POST", "GET"])
def groupchat():
    username = session.get("username")
    room = session.get("room")

    # displaying old groups
    user_groups = []
    user_groups_dic = db.execute(
        "SELECT code FROM groups WHERE member = ?" , (username,)
    ).fetchall()

    for group in user_groups_dic:
        user_groups.append(group[0])

    # displaying old messages
    chats = []
    chat_dic = db.execute("SELECT * FROM messages WHERE code = ?", (session["room"],))

    for messages in chat_dic:
        chatings = {
            "username": messages[1],
            "message": messages[2],
            "time": messages[3],
            "image": messages[4],
        }
        chats.append(chatings)

    return render_template("group.html", chats=chats, room=room, username=username, user_groups=user_groups)


@app.route("/profile", methods=["POST", "GET"])
def profile():
    # selecting users data
    user_data = []
    user_data_dic = db.execute(
        "SELECT username,image FROM users WHERE username = ?",
        (session.get("username"),),
    ).fetchall()
    for user in user_data_dic:
        data = {
            "username": user[0],
            "image": user[1],
        }
        user_data.append(data)

    return render_template("profile.html", user_data=user_data)


@app.route("/profilepic", methods=["POST", "GET"])
def profilepic():
    if request.method == "POST":
        username = session.get("username")
        image = request.form.get("pic")
        # updating user image
        if image:
            db.execute(
                "UPDATE users SET image = ? WHERE username = ?", (image, username)
            )
            db.execute(
                "UPDATE messages SET image = ? WHERE sender = ?", (image, username)
            )
            conn.commit()
            session["image"] = image
            return redirect("/profile")

    user_data = []
    user_data_dic = db.execute(
        "SELECT username,image FROM users WHERE username = ?",
        (session.get("username"),),
    ).fetchall()
    for user in user_data_dic:
        data = {
            "username": user[0],
            "image": user[1],
        }
        user_data.append(data)

    change = "profilepic"
    return render_template("profile.html", change=change, user_data=user_data)


@app.route("/delete_account", methods=["POST", "GET"])
def delete_account():
    user_data = []
    user_data_dic = db.execute(
        "SELECT username,image FROM users WHERE username = ?",
        (session.get("username"),),
    ).fetchall()
    for user in user_data_dic:
        data = {
            "username": user[0],
            "image": user[1],
        }
        user_data.append(data)

    change = "deleteaccount"

    if request.method == "POST":
        username = session.get("username")
        password = request.form.get("password")

        # checking password
        if password:
            user_password = db.execute(
                "SELECT hash FROM users WHERE username = ?", (username,)
            ).fetchall()

            if not check_password_hash(user_password[0][0], password):
                error = "Incorrect Password!"
                return render_template(
                    "profile.html", change=change, user_data=user_data, error=error
                )

            # deleting user belongings
            else:
                db.execute("DELETE FROM users WHERE username = ?", (username,))
                db.execute("DELETE FROM messages WHERE sender = ?", (username,))
                db.execute(
                    "DELETE FROM contacts WHERE code LIKE ?", ("%" + "-" + username,)
                )
                db.execute(
                    "DELETE FROM contacts WHERE code LIKE ?", (username + "-" + "%",)
                )
                db.execute("DELETE FROM friends WHERE username = ?", (username,))
                db.execute("DELETE FROM friends WHERE friend = ?", (username,))
                db.execute("DELETE FROM groups WHERE member = ?", (username,))
                conn.commit()

                return redirect("/login")

    return render_template("profile.html", change=change, user_data=user_data)


@app.route("/change_password", methods=["POST", "GET"])
def change_password():
    user_data = []
    user_data_dic = db.execute(
        "SELECT username,image FROM users WHERE username = ?",
        (session.get("username"),),
    ).fetchall()
    for user in user_data_dic:
        data = {
            "username": user[0],
            "image": user[1],
        }
        user_data.append(data)

    change = "changepassword"

    if request.method == "POST":
        username = session.get("username")
        password = request.form.get("password")
        new_password = request.form.get("new_password")
        new_confirmation = request.form.get("new_confirmation")

        if password:
            user_password = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchall()

            if not check_password_hash(user_password[0][2], password):
                error = "Incorrect Password!"
                return render_template(
                    "profile.html", change=change, user_data=user_data, error=error
                )

            else:
                if new_password != new_confirmation:
                    error = "Password doesn't match!"
                    return render_template(
                        "profile.html", change=change, user_data=user_data, error=error
                    )

                else:
                    # encrypting the new password
                    hash = generate_password_hash(new_password)

                    # updating users table
                    db.execute(
                        "UPDATE users SET hash = ? WHERE username = ?",
                        (
                            hash,
                            username,
                        ),
                    )

                return redirect("/login")

    return render_template("profile.html", change=change, user_data=user_data)


@app.route("/mood", methods=["POST", "GET"])
def mood():
    username = session.get("username")
    if request.method == "POST":
        username = session.get("username")
        username_mood = request.form.get("mood")
        username_status = request.form.get("status")
        # selecting user mood
        if username_mood:
            db.execute(
                "UPDATE users SET mood = ? WHERE username = ?",
                (username_mood, username),
            )
            db.execute(
                "UPDATE users SET status = ? WHERE username = ?",
                (username_status, username),
            )
            conn.commit()
            session["mood"] = username_mood
            return redirect("/status")

    # displaying moods to select from
    moods = []
    moods_dic = db.execute("SELECT * FROM moods ORDER BY mood")
    for moood in moods_dic:
        mood = {"mood": moood[0], "status": moood[1]}
        moods.append(mood)

    # displaying user selected mood
    user_mood = []
    user_moods_dic = db.execute(
        "SELECT * FROM moods WHERE mood = ?", (session.get("mood"),)
    )
    for moood in user_moods_dic:
        mood = {"mood": moood[0], "status": moood[1]}
        user_mood.append(mood)

    return render_template("mood.html", moods=moods, user_mood=user_mood)


@app.route("/status")
def status():
    friends = db.execute(
        "SELECT friend FROM friends WHERE username = ?", (session.get("username"),)
    ).fetchall()
    all_status = []
    # displaying your status
    user_status_dic = db.execute(
        "SELECT username, mood, status FROM users WHERE username = ?",
        (session.get("username"),),
    ).fetchall()
    for status in user_status_dic:
        user_status = {
            "username": status[0],
            "mood": status[1],
            "status": status[2],
        }
        all_status.append(user_status)

    # displaying friends status
    for friend in friends:
        all_status_dic = db.execute(
            "SELECT username, mood, status FROM users WHERE username = ?", (friend[0],)
        ).fetchall()
        for status in all_status_dic:
            user_status = {
                "username": status[0],
                "mood": status[1],
                "status": status[2],
            }
            all_status.append(user_status)

    # which is the most chosen mood
    mood_counts = []
    counts = []
    selected_mood_dic = db.execute("SELECT DISTINCT mood,status FROM users").fetchall()
    for mood in selected_mood_dic:
        mood_count = db.execute(
            "SELECT COUNT(mood),status FROM users WHERE mood = ?", (mood[0],)
        ).fetchall()
        mood_counts.append(
            {"mood": mood[0], "count": mood_count[0][0], "status": mood[1]}
        )
        counts.append(mood_count[0][0])

    for mood in mood_counts:
        if mood["count"] == max(counts):
            most_status = {
                "mood": mood["mood"],
                "status": mood["status"],
            }
            break

    return render_template(
        "status.html", all_status=all_status, most_status=most_status
    )


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect("/login")


# socket connections
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    join_room(room)


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    leave_room(room)


@socketio.on("message")
def message(data):
    room = session.get("room")
    content = {
        "username": session.get("username"),
        "message": data["data"],
        "time": datetime.now().strftime("%I:%M:%p").lower(),
        "image": session.get("image"),
    }

    message_data = data["data"]

    # inserting message data into the database
    db.execute(
        "INSERT INTO messages(code, sender,message, time, image) VALUES(?,?,?,?,?)",
        (
            room,
            session.get("username"),
            message_data,
            datetime.now().strftime("%I:%M:%p").lower(),
            session.get("image"),
        ),
    )
    conn.commit()

    send(content, to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
