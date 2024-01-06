#!/usr/bin/node

var token = window.localStorage.getItem('token')

function showShell(typ=null) {
    // $("#form").html('<textarea style="width: 80%; height: 400px;" id="box">Starting bot...</textarea>')
    
    if (typ === "start") {
        $("#form").html('<textarea readonly style="width: 80%; height: 500px;" id="box">Starting bot...</textarea>')
        setTimeout(() => {}, 5000);
    } else if (typ === 'end') {
        var exist = $("#box").val()
        exist = exist + '\n\nBot stopped'
        $("#box").text(exist)
        intervalId = window.localStorage.getItem("intervalId");
        clearInterval(intervalId)
        window.localStorage.removeItem("intervalId")
        return
    } else if (typ != null) {
        var exist = $("#box").val()
        exist = exist + '\n\nBot stopped'
        $("#box").text(exist)
        intervalId = window.localStorage.getItem("intervalId");
        clearInterval(intervalId)
        return;
    }
    function get_bot_msg() {
        bot_id = window.localStorage.getItem("bot_id")
        request.get('/get-bot-msg/' + bot_id)
        .then((data) => {
            if (data === null) {
                return;
            }
            var exist = $("#box").val()
            for (dt of data) {
                exist = exist + '\n\n' + dt
                if (dt === "Bot stopped") {
                    showShell("end");
                    return;
                } else {
                    $("#box").text(exist);
                }
            }
            
            return data;
        }).catch((err) => {
            errorHandler(err, "Error getting notifications");
        })
    }
    var intervalId = setInterval(get_bot_msg, 8000)
    window.localStorage.setItem("intervalId", intervalId)
}

function get_key(exchange) {
    request.get('/get_keys')
    .then((data) => {
        if (data != null) {
            // $("#api-key").val(data.gate_key)
            // $("#secret").val(data.gate_secret);
            $("#api-key").val(data[exchange + "_key"])
            $("#secret").val(data[exchange + "_secret"])
            // $("#uid").val(data[exchange + "_uid"])
            // $("#password").val(data[exchange + "_password"])
        }
    }).catch((err) => {
        errorHandler(err, "Could not fetch keys");
    })
}

get_key("gate")

function adjustTextArea() {
    const textarea = document.getElementById('token');
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

$(function get_coins() {
    var mexcCoins = []
    var gateCoins = []
    request.get('/get-coins')
    .then((data) => {
        $.each(data, (_idx, token) => {
            if (token.exchange === "gate") {
                gateCoins.push(token);
            } else if (token.exchange === "mexc") {
                mexcCoins.push(token);
            }
        })
        var mexcSection = "Mexc tokens:\n"
        $.each(mexcCoins, (_idx, token) => {
            mexcSection = mexcSection + `${token.symbol} --- ${token.listing_date}\n`
        })
        mexcSection = mexcSection + `\n-----------------------------------\n`
        var gateSection = "Gate.io tokens:\n"
        $.each(gateCoins, (_idx, token) => {
            gateSection = gateSection + `${token.symbol} --- ${token.listing_date}\n`
        });
        var allCoins = mexcSection + gateSection;
        // var exists = $("#token").val();
        // exists = exists + `${token.symbol} --- ${token.listing_date}\n`
        $("#token").val(allCoins);
        adjustTextArea()
    })
})

$(function get_bots() {
    request.get('/get-user-bots')
    .then((data) => {
        if (data === null) {
            $("#existing_bots").addClass('disappear');
        } else {
            $(".new_bot").addClass('disappear');
            window.localStorage.setItem("bot_id", data[0])
            $("#existing_bots").html(`<p>You have ${data.length} active bot, 
                click <a href='/static/trade-page.html'>here</a> to view<p>`)
        }
    })
})

$("#exchange").on('change', () => {
    if (['binance', 'bingx', 'bitmex', 'bybit', 'gate', 'huobi', 'mexc'].includes($("#exchange :selected").val())) {
        $("#keys").html(`<input id="api-key" placeholder="API-key"><br>
        <input id="secret" placeholder="API-secret"><br><br>`)
    } else if (['bitget', 'kucoin', 'okx'].includes($("#exchange :selected").val())) {
        $("#keys").html(`<input id="api-key" placeholder="API-key"><br>
            <input id="secret" placeholder="API-secret"><br>
            <input id="password" placeholder="Passphrase"><br><br>`)
    } else if ($("#exchange :selected").val() === 'bitmart') {
        $("#keys").html(`<input id="api-key" placeholder="API-key"><br>
        <input id="secret" placeholder="API-secret"><br>
        <input id="uid" placeholder="Memo"><br><br>`)
    }
    get_key($("#exchange :selected").val())
})

$("#save").on('click', () => {
    $("#save").addClass('disappear');
    var payload = {
        'capital': $("#capital").val(),
        'apiKey': $("#api-key").val(),
        'secret': $("#secret").val(),
        'exchange': $("#exchange").val()
    };
    // if (['bitget', 'gate', 'kucoin', 'okex'].includes($("#exchange").val())) {
    //     payload['password'] = $("#password").val()
    // } else if ($("#exchange").val() === 'bitmart') {
    //     payload['uid'] = $("#uid").val()
    // }
    payload = JSON.stringify(payload);
    request.post('/start-trade', payload)
    .then((data) => {
        // $("#start").removeClass('disappear');
        $("#stop").removeClass('disappear');
        window.localStorage.setItem("bot_id", data.bot_id);
        window.localStorage.setItem("shellStatus", "start");
        window.location.href = "trade-page.html"
        // $("#form").html(`<textarea readonly style="width: 80%; height: 500px;" id="box"></textarea>`)
        // showShell("start")
    }).catch((err) => {
        $("#save").removeClass('disappear');
        errorHandler(err, "An error has occured")
    })
})

$("#start").on('click', () => {
    bot_id = window.localStorage.getItem("bot_id");
    $("#start").addClass('disappear');
    $("#stop").removeClass('disappear');
    showShell("start")

    request.get('/start/' + bot_id)
    .then(() => {
        $("#form").html('<textarea readonly style="width: 80%; height: 500px;" id="box">Your bot has been activated</textarea>')
    }).catch((err) => {
        // console.log(err.toString());
        console.log(err.responseText)
        errorHandler(err, "Error starting bot")
        showShell("end");
    })
})

$("#stop").on('click', () => {
    bot_id = window.localStorage.getItem('bot_id');
    $("#stop").addClass("disappear")
    request.destroy('/stop-trade/' + bot_id)
    .then(() => {
        showShell("end");
    }).catch((err) => {
        errorHandler(err, "An error has occured")
    })
})
