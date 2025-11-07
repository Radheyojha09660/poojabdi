// Simple cart in localStorage and updates cart counter
function getCart(){
  return JSON.parse(localStorage.getItem('poojabdi_cart')||'[]');
}
function saveCart(c){
  localStorage.setItem('poojabdi_cart', JSON.stringify(c));
  renderCartCount();
}
function addToCart(id, title, price){
  let c = getCart();
  let item = c.find(x=>x.id===id);
  if(item) item.qty++;
  else c.push({id:id, title:title, price:price, qty:1});
  saveCart(c);
  alert('Added to cart');
}
function renderCartCount(){
  let c = getCart();
  let total = c.reduce((s,i)=>s+i.qty,0);
  let el = document.getElementById('cart-count');
  if(el) el.textContent = total;
}
function renderCartItems(){
  let items = getCart();
  let container = document.getElementById('cart-items');
  if(!container) return;
  container.innerHTML = '';
  if(items.length===0){ container.innerHTML = '<div class="bg-white p-4 rounded">Cart is empty</div>'; return; }
  items.forEach(it=>{
    let div = document.createElement('div');
    div.className = 'bg-white p-4 rounded flex justify-between items-center';
    div.innerHTML = `<div><div class="font-semibold">${it.title}</div><div class="text-sm text-gray-500">Qty: ${it.qty}</div></div><div>₹${(it.price*it.qty).toFixed(2)}</div>`;
    container.appendChild(div);
  });
}
window.addEventListener('load', ()=>{ renderCartCount(); renderCartItems();
  let btn = document.getElementById('checkout-btn');
  if(btn) btn.addEventListener('click', ()=>{ alert('Order submitted (demo). Integrate with backend or payment gateway to complete purchase).'); localStorage.removeItem('poojabdi_cart'); renderCartCount(); renderCartItems(); });
});
