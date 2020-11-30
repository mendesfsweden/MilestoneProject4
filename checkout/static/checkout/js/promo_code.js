$('#btn-promo-code').click(ev => {
    ev.preventDefault()
    const promo = $('#input-promo-code').val()
    const url = new URL(window.location)
    url.searchParams.set('promo-code', promo)
    window.location.replace(url)
})