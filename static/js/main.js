document.addEventListener('DOMContentLoaded', function() {
  const cards = document.querySelectorAll('.card');
  cards.forEach((c, i) => {
    c.style.opacity = 0;
    setTimeout(()=> {
      c.style.transition = 'opacity 420ms ease, transform 420ms ease';
      c.style.opacity = 1;
      c.style.transform = 'translateY(0)';
    }, 80 * i);
  });

  document.querySelectorAll('.inline-input').forEach(inp=>{
    inp.addEventListener('change', async (e)=>{
      const id = e.target.dataset.id;
      const data = {};
      if(e.target.classList.contains('name-input')) data.name = e.target.value;
      if(e.target.classList.contains('price-input')) data.price = e.target.value;
      try {
        const res = await fetch('/api/update_product/' + id, {
          method: 'POST',
          body: new URLSearchParams(data),
          credentials: 'same-origin'
        });
        const j = await res.json();
        if(j.status !== 'ok') alert('Update failed');
      } catch(err) {
        console.error(err);
        alert('Network error');
      }
    });
  });
});
