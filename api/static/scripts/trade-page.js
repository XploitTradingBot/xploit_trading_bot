#!/usr/bin/node

var token = window.localStorage.getItem('token')
var shellStatus = window.localStorage.getItem('shellStatus')

function showShell(typ=null) {
    if (typ === "start") {
        $("#box").text('Starting bot...')
        setTimeout(() => {}, 5000);
    } else if (typ === 'end') {
        var exist = $("#box").val()
        exist = exist + '\n\nBot stopped'
        $("#box").text(exist)
        $("#stop").addClass('disappear');
        intervalId = window.localStorage.getItem("intervalId");
        clearInterval(intervalId);
        window.localStorage.removeItem("intervalId");
        return;
    } else {
        $("#box").text('Bot is active');
        var bot_id = window.localStorage.getItem("bot_id");
        request.get('/get-bot-msg/' + bot_id + '?show_read=1')
        .then((data) => {
            if (data === null) {
                return;
            }
            var exist = $("#box").val()
            for (dt of data) {
                if (dt === "Bot stopped") {
                    $("#box").text(exist);
                    showShell("end");
                    return;
                } else {
                    exist = exist + '\n\n' + dt
                    $("#box").text(exist);
                }
            }
        })
    }
    function get_bot_msg() {
        bot_id = window.localStorage.getItem("bot_id");
        request.get('/get-bot-msg/' + bot_id)
        .then((data) => {
            if (data === null) {
                return;
            }
            var exist = $("#box").val()
            for (dt of data) {
                if (dt === "Bot stopped") {
                    $("#box").text(exist);
                    showShell("end");
                    return;
                } else {
                    exist = exist + '\n\n' + dt
                    $("#box").text(exist);
                }
            }
            return data;
        }).catch((err) => {
            errorHandler(err, "Error getting notifications");
            showShell("end")
        })
    }
    var intervalId = setInterval(get_bot_msg, 5000)
    window.localStorage.setItem("intervalId", intervalId)
}

if (shellStatus === "start") {
    window.localStorage.setItem("shellStatus", "continue")
    showShell("start");
} else {
    showShell();
}

$("#stop").on('click', () => {
    bot_id = window.localStorage.getItem('bot_id');
    $("#stop").addClass("disappear")
    request.destroy('/stop-trade/' + bot_id)
    .then(() => {
        showShell("end");
    }).catch((err) => {
        if (err.status === 500) {
            showShell("end");
        } else {
            errorHandler(err, "An error has occured");
            $("#stop").removeClass("disappear");
        }
    })
})
