/* main.js - minimal frontend for products + cart + admin hooks */
document.addEventListener('DOMContentLoaded', function(){
  // fetch & render products
  function fetchProducts(){
    fetch('/products.json').then(r=>r.json()).then(renderProducts).catch(err=>console.error(err));
  }

  function renderProducts(products){
    const grid = document.getElementById('products-grid');
    grid.innerHTML = '';
    products.forEach(p=>{
      const imgSrc = p.img || '/static/images/no-image.png';
      const div = document.createElement('div'); div.className='product';
      div.innerHTML = `<img src="${imgSrc}" onerror="this.src='/static/images/no-image.png'"><h4>${p.name_hi || p.name_en}</h4><div class="price">${p.price || ''}</div><div style="margin-top:10px"><button class="btn primary add" data-id="${p.id}">कार्ट में जोड़ें</button></div>`;
      grid.appendChild(div);
    });
    document.querySelectorAll('.add').forEach(b => b.addEventListener('click', function(e){
      const id = Number(this.dataset.id);
      fetch('/api/cart', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:id, qty:1})})
        .then(()=> updateCartCount());
    }));
  }

  function updateCartCount(){
    fetch('/api/cart').then(r=>r.json()).then(cart=>{
      const count = Object.values(cart).reduce((s,v)=>s+v,0);
      const el = document.getElementById('cart-count');
      if(el) el.innerText = count;
    });
  }

  // admin: add product via form (admin_panel page)
  const prodForm = document.querySelector('#product-form');
  if(prodForm){
    prodForm.addEventListener('submit', function(e){
      e.preventDefault();
      const form = new FormData(prodForm);
      fetch('/admin/api/product', {method:'POST', body: form})
        .then(r=>r.json())
        .then(res=>{
          if(res.ok) location.reload();
        }).catch(err=>console.error(err));
    });
  }

  // admin: delete/edit handlers
  document.querySelectorAll('.delete').forEach(btn=>{
    btn.addEventListener('click', function(){
      const id = this.dataset.id;
      if(!confirm('Delete product?')) return;
      fetch('/admin/api/product', {method:'DELETE', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id: id})})
        .then(r=>r.json()).then(res=> { if(res.ok) location.reload(); });
    });
  });
  document.querySelectorAll('.edit').forEach(btn=>{
    btn.addEventListener('click', function(){
      const id = this.dataset.id;
      const name_hi = prompt('Name (HI)');
      if(name_hi === null) return;
      const name_en = prompt('Name (EN)');
      if(name_en === null) return;
      const price = prompt('Price (e.g., ₹60 / 250g)') || '';
      const price_num = prompt('Price numeric (60)') || '0';
      const img = prompt('Image URL or dataURL') || '';
      const fd = new FormData();
      fd.append('id', id);
      fd.append('name_hi', name_hi);
      fd.append('name_en', name_en);
      fd.append('price', price);
      fd.append('price_num', price_num);
      fd.append('img', img);
      fetch('/admin/api/product', {method:'PUT', body: fd})
        .then(r=>r.json()).then(res=> { if(res.ok) location.reload(); });
    });
  });

  // site info save (admin panel)
  const siteForm = document.getElementById('site-form');
  if(siteForm){
    siteForm.addEventListener('submit', function(e){
      e.preventDefault();
      const fd = new FormData(siteForm);
      fetch('/admin/api/settings', {method:'POST', body: fd})
        .then(r=>r.json()).then(res=>{ if(res.ok){ alert('Saved'); }});
    });
  }

  // cart UI - simple open/close
  const cartBtn = document.getElementById('cart-btn');
  const cartDrawer = document.getElementById('cart-drawer');
  const cartOverlay = document.getElementById('cart-overlay');
  if(cartBtn){
    cartBtn.addEventListener('click', function(){ openCart(); });
  }
  function openCart(){ cartDrawer.classList.add('open'); cartOverlay.classList.add('visible'); loadCartItems(); }
  function closeCart(){ cartDrawer.classList.remove('open'); cartOverlay.classList.remove('visible'); }
  const cartClose = document.getElementById('cart-close');
  if(cartClose) cartClose.addEventListener('click', closeCart);
  if(cartOverlay) cartOverlay.addEventListener('click', closeCart);

  function loadCartItems(){
    fetch('/api/cart').then(r=>r.json()).then(cart=>{
      const wrap = document.getElementById('cart-items');
      wrap.innerHTML = '';
      let subtotal = 0;
      fetch('/products.json').then(r=>r.json()).then(products=>{
        Object.entries(cart).forEach(([pid, qty])=>{
          const prod = products.find(p=>String(p.id)===String(pid));
          if(!prod) return;
          const price = Number(prod.price_num || parseFloat(String(prod.price||'').replace(/[^\d.]/g,'')) || 0);
          subtotal += price * qty;
          const div = document.createElement('div'); div.className='cart-item';
          div.innerHTML = `<img src="${prod.img||'/static/images/no-image.png'}" onerror="this.src='/static/images/no-image.png'"><div style="flex:1"><div style="font-weight:700">${prod.name_hi||prod.name_en}</div><div style="color:var(--muted)">${prod.price||''}</div><div style="margin-top:6px;display:flex;gap:8px;align-items:center"><button class="btn ghost qty-dec">-</button><div class="qty">${qty}</div><button class="btn ghost qty-inc">+</button></div></div><div style="text-align:right"><div style="font-weight:700;color:var(--gold)">${'₹'+(price*qty).toFixed(2)}</div><button class="btn ghost remove-item" style="margin-top:8px">Remove</button></div>`;
          wrap.appendChild(div);
          div.querySelector('.qty-inc').addEventListener('click', ()=> changeQty(pid, qty+1));
          div.querySelector('.qty-dec').addEventListener('click', ()=> changeQty(pid, qty-1));
          div.querySelector('.remove-item').addEventListener('click', ()=> removeFromCart(pid));
        });
        document.getElementById('cart-subtotal').innerText = '₹' + subtotal.toFixed(2);
      });
    });
  }

  function changeQty(pid, newQty){
    if(newQty <= 0) return removeFromCart(pid);
    // replace cart via POST multiple times: simplest approach to update server session
    // We'll read existing cart, set new qty and write via API by clearing & re-adding - keeping simple:
    fetch('/api/cart').then(r=>r.json()).then(cart=>{
      cart[pid] = newQty;
      // clear session on server then re-add items
      // For simplicity here we emulate by deleting then adding items accordingly
      // Better approach: implement PUT endpoint server-side; but current API limited - so we call DELETE then POST repeatedly
      // We'll just call a DELETE for pid then POST with qty
      fetch('/api/cart', {method:'DELETE', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id: pid})})
        .then(()=> fetch('/api/cart', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id: pid, qty: newQty})}))
        .then(()=> { updateCartCount(); loadCartItems(); });
    });
  }

  function removeFromCart(pid){
    fetch('/api/cart', {method:'DELETE', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id: pid})})
      .then(()=> { updateCartCount(); loadCartItems(); });
  }

  // init
  fetchProducts(); updateCartCount();
});
