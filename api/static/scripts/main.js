#!/usr/bin/node

token = window.localStorage.getItem("token")

class Request {
    constructor() {
        // this.api = "http://localhost:8000/bot"
        this.api = "https://trading-bot-qs90.onrender.com/bot"
    }

    get(endpoint) {
        return new Promise((res, rej) => {
            $.ajax({
                type: 'GET',
                url: this.api + endpoint,
                contentType: 'application/json',
                headers: {
                    'Authorization': "TradingBot " + token
                },
                crossDomain: true,
                dataType: 'json',
                success: function(data) {
                    res(data);
                },
                error: function(err) {
                    rej(err);
                }
            })
        })
    }
    post(endpoint, payload) {
        return new Promise((res, rej) => {
            $.ajax({
                type: 'POST',
                url: this.api + endpoint,
                contentType: 'application/json',
                headers: {
                    'Authorization': "TradingBot " + token
                },
                data: payload,
                crossDomain: true,
                dataType: 'json',
                success: function(data) {
                    res(data);
                },
                error: function(err) {
                    rej(err);
                }
            })
        })
    }
    destroy(endpoint) {
        return new Promise((res, rej) => {
            $.ajax({
                type: 'DELETE',
                url: this.api + endpoint,
                contentType: 'application/json',
                headers: {
                    'Authorization': "TradingBot " + token
                },
                crossDomain: true,
                dataType: 'json',
                success: function(data) {
                    res(data);
                },
                error: function(err) {
                    rej(err);
                }
            })
        })
    }
}

request = new Request()

function errorHandler(err, info) {
    if (err.status === 500 || err.status === 502) {
        window.location.reload()
    } else if (err.status === 401) {
        window.location.href = "login.html"
    } else if (err.responseJSON) {
        alert(err.responseJSON)
    } else {
        alert(info)
        console.log(err);
    }
}
