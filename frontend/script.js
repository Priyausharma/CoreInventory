function updateStock(){

let name = document.getElementById("pname").value
let sku = document.getElementById("sku").value
let category = document.getElementById("category").value
let qty = parseInt(document.getElementById("stock").value)

let action = document.getElementById("action").value

let table = document.getElementById("inventoryTable")
let rows = table.rows
let found = false

for(let i=1;i<rows.length;i++){

if(rows[i].cells[0].innerHTML == name){

let currentStock = parseInt(rows[i].cells[3].innerHTML)

if(action=="add"){
currentStock += qty
}else{
currentStock -= qty
}

rows[i].cells[3].innerHTML = currentStock

found = true
break

}

}

if(!found){

let row = table.insertRow()

row.insertCell(0).innerHTML = name
row.insertCell(1).innerHTML = sku
row.insertCell(2).innerHTML = category

if(action=="add"){
row.insertCell(3).innerHTML = qty
}else{
row.insertCell(3).innerHTML = -qty
}

}

let movement = document.getElementById("movementList")
let item = document.createElement("li")

if(action=="add"){
item.innerText = name + " stock added: " + qty
}else{
item.innerText = name + " stock removed: " + qty
}

movement.appendChild(item)

alert("Stock Updated Successfully")

document.getElementById("pname").value=""
document.getElementById("sku").value=""
document.getElementById("category").value=""
document.getElementById("stock").value=""

}
