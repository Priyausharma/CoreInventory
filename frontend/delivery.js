let deliveries = []

function deliverProduct(){

let name = document.getElementById("productName").value
let sku = document.getElementById("sku").value
let qty = document.getElementById("qty").value

let delivery = {
name:name,
sku:sku,
qty:qty
}

deliveries.push(delivery)

updateDeliveryTable()

alert("Product Delivered Successfully")

clearForm()

}

function updateDeliveryTable(){

let table = document.getElementById("deliveryTable")

let row = table.insertRow()

row.insertCell(0).innerHTML = deliveries[deliveries.length-1].name
row.insertCell(1).innerHTML = deliveries[deliveries.length-1].sku
row.insertCell(2).innerHTML = deliveries[deliveries.length-1].qty

}

function clearForm(){

document.getElementById("productName").value=""
document.getElementById("sku").value=""
document.getElementById("qty").value=""

}
