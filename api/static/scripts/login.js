#!/usr/bin/node


$("#login").on('click', () => {
    var email = $("#email").val();
    var password = $("#password").val();

    var payload = JSON.stringify({"email": email, "password": password})

    request.post('/user/login', payload)
    .then((data) => {
        console.log(data);
        alert(`Welcome back ${data.name}`)
        window.localStorage.setItem('token', data.token)
        window.location.href = "bot-page.html";
    }).catch((err) => {
        errorHandler(err, "Error encountered while signing in");
    })
})