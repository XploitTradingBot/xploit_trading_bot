#!/usr/bin/node


$("#submit").on('click', function() {
    var name = $("#name").val();
    var email = $("#email").val();
    var password = $("#password").val()
    var payload = JSON.stringify({"name": name, "email": email, "password": password});

    request.post('/users', payload)
    .then((data) => {
        alert(`Welcome ${data.name}`)
        window.localStorage.setItem('token', data.token)
        window.location.href = "bot-page.html";
    }).catch((err) => {
        errorHandler(err, "An error occured")
    })
})