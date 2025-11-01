// minimal frontend JS: fetch products, render, cart actions
document.addEventListener('DOMContentLoaded', function(){
  let siteLang = localStorage.getItem('siteLang')||'hi';
  function placeholder(){ return ''; }
  function fetchProducts(){
    fetch('/products.json').then(r=>r.json()).then(renderProducts);
  }
  function renderProducts(products){
    const grid = document.getElementById('products-grid');
    grid.innerHTML = '';
    products.forEach(p=>{
      const div = document.createElement('div'); div.className='product';
      div.innerHTML = `<img src="${p.img||''}" onerror="this.src='';"><h4>${siteLang==='hi'?p.name_hi:p.name_en}</h4><div class="price">${p.price||''}</div><div style="margin-top:10px"><button class="btn primary add" data-id="${p.id}">${siteLang==='hi'?'कार्ट में जोड़ें':'Add to Cart'}</button></div>`;
      grid.appendChild(div);
    });
    document.querySelectorAll('.add').forEach(b=> b.addEventListener('click', e=>{
      const id = Number(e.currentTarget.dataset.id);
      fetch('/api/cart', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:id, qty:1})}).then(()=>updateCartCount());
    }));
  }
  function updateCartCount(){
    fetch('/api/cart').then(r=>r.json()).then(cart=>{
      const count = Object.values(cart).reduce((s,v)=>s+v,0);
      document.getElementById('cart-count').innerText = count;
    });
  }
  document.getElementById('cart-btn').addEventListener('click', ()=> alert('Open cart drawer on deployed site'));
  fetchProducts(); updateCartCount();
});
