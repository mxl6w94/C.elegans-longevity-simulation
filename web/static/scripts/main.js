// Wild type means "no genes changed", so it can't be ticked together with a gene.
// Ticking one side clears the other. The server checks this too, for browsers without JavaScript.
document.addEventListener("DOMContentLoaded", () => {
  const boxes = Array.from(document.querySelectorAll('input[name="genes"]'));
  const wildType = boxes.find((b) => b.hasAttribute("data-wild-type"));
  if (!wildType) return;
  const genes = boxes.filter((b) => b !== wildType);

  wildType.addEventListener("change", () => {
    if (wildType.checked) genes.forEach((g) => (g.checked = false));
  });
  genes.forEach((g) =>
    g.addEventListener("change", () => {
      if (g.checked) wildType.checked = false;
    })
  );
});
