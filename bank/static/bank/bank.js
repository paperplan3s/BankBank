
document.addEventListener('DOMContentLoaded', function() {

  // When making an external transfer, display the details of the transfer as the user finishes inputting the details
  let rcvr = document.getElementById("id_receiver");
  let amount = document.getElementById("id_amount");
  amount.onchange = function() {
  if (rcvr.value != ''){
      rcvr = rcvr.value
      rcvr =  rcvr.charAt(0).toUpperCase() + rcvr.slice(1);
      amount = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount.value);
      document.getElementById("details").innerHTML = `Transferring ${amount} to ${rcvr}.`;
    }
    else{
      document.getElementById("details").innerHTML = "Please enter a username.";
    }
  };



  // Handles users adding and changing categories attached to their transactions
   document.querySelectorAll('.catbutton').forEach(function(cat) {

     cat.addEventListener("click", function() {
       let tryid = `cat${cat.id}`
       let display = document.getElementById(tryid);
       display.innerHTML = `<form id="${cat.id}" onsubmit="return false;"> <select id="catselect"><option value="Housing">Housing</option><option value="Transport">Transport</option><option value="Grocery">Grocery</option><option value="Utilities">Utilities</option><option value="Insurance">Insurance</option><option value="Medical">Medical</option><option value="Recreation">Recreation</option><option value="Miscellaneous">Miscellaneous</option><option value="Income">Income</option></select><input class="catSubmit" id="{{transaction.id}}" style="width: 60%;" type="submit" value="Save"></form>`;

       display.addEventListener("submit", (e) => {

         e.preventDefault();
         let option = document.getElementById("catselect").value;
          let catbox = document.getElementById(event.srcElement.id)
         categorize(event.srcElement.id, option);
         catbox.innerHTML = `<form id="${cat.id}" onsubmit="return false;"> ${option}<input class="catSubmit" id="{{transaction.id}}" style="width: 20%; color:white;" type="submit" value=""></form>`;
         return false;
       });
    });

     // makes a call to the Categorize APi
     function categorize(id, option) {
      event.preventDefault();
       let transaction = id;
       let category = option;
       let url_path = `/categorize`;
       fetch(url_path, {
             method: 'PUT',
             body: JSON.stringify({
               transaction: transaction,
               category: category
             })
           });
           return false
       }

       // Makes a request to the Internal Transfer API
   function int_transfer(id) {
    event.preventDefault();
     let account = document.querySelector('#transferaccount').value;
     let amount = document.querySelector('#transferamount').value;
     let url_path = `/inttransfer`;
     fetch(url_path, {
           method: 'POST',
           body: JSON.stringify({
             account: account,
             amount: amount
           })
         });
         return false
     }

     ;})
    });
