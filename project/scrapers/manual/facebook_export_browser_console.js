(() => {
  const articles = Array.from(document.querySelectorAll('[role="article"]'));
  const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
  const posts = articles
    .map((article) => {
      const text = clean(article.innerText);
      const links = Array.from(article.querySelectorAll('a[href]')).map((link) => link.href);
      const postUrl =
        links.find((href) => /\/groups\/\d+\/posts\//.test(href)) ||
        links.find((href) => /\/posts\//.test(href)) ||
        '';
      const imageUrls = Array.from(article.querySelectorAll('img[src]'))
        .map((image) => image.src)
        .filter((src) => /fbcdn\.net|scontent/i.test(src));
      const author =
        clean(article.querySelector('h2, h3, strong')?.innerText) ||
        clean(article.querySelector('a[role="link"]')?.innerText);

      return {
        author,
        date: new Date().toISOString().slice(0, 10),
        url: postUrl,
        text,
        imageUrls: Array.from(new Set(imageUrls)).slice(0, 6),
      };
    })
    .filter((post) => post.text.length > 80);

  const blob = new Blob([JSON.stringify(posts, null, 2)], { type: 'application/json' });
  const anchor = document.createElement('a');
  anchor.href = URL.createObjectURL(blob);
  anchor.download = 'facebook_group_posts.json';
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
  console.log(`Exported ${posts.length} visible Facebook posts.`);
})();
