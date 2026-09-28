/* Kataki · App screens · shared support for every artboard on this canvas.
   1. Points the design system's art (portraits, places, clouds) at this canvas's own copies.
   2. Maps the rail and other shared links to the artboards that stand for each route.
   3. Builds design-system elements for slot props (actions, footers, composer) that markup cannot pass. */
(function () {
  var ART = {
    liv: 'e49764b15e9de5d49d4bc2bbf8c90f65',
    mike: '0b9fe4d5e949fe7395d2dc331675abe8',
    theo: '24f537101f1220b0706482e827c12368',
    jae: '98b8803c4f86e4c451df752de430a773',
    nico: '88294483e380df3b0fb980ee2c0b5d07',
    cas: '6ee3bde163b8abc870ce59996374605d',
    'halcyon-coffee': '1e023859469874b847f3f6c9eb3831a9',
    'corvel-palace': 'f9ee926a93a1e0c21681768006f8293a',
    'flat-on-ardenne': '27e72542c91efd72118b0f88c6bac4a7',
    clouds: 'e207af2b3e316bdbc66fc7d1e4f92cc4'
  };
  function patch() {
    var K = window.Kataki;
    if (!K || !K.ART || K.__appArt) return !!(K && K.__appArt);
    Object.keys(ART).forEach(function (k) { K.ART[k] = Object.assign({}, K.ART[k], { src: '/_blob/' + ART[k] }); });
    K.__appArt = true;
    return true;
  }
  if (!patch()) {
    document.addEventListener('DOMContentLoaded', patch);
    var tries = 0, t = setInterval(function () { if (patch() || ++tries > 40) clearInterval(t); }, 50);
  }

  /* Routes → the artboard that draws each one. */
  var HREFS = {
    Home: 'Home.dc.html', Stories: 'Stories.dc.html', Characters: 'Characters.dc.html', World: 'World.dc.html', You: 'You.dc.html',
    'New character': 'NewCharacter.dc.html', Settings: 'SetGeneral.dc.html', Feedback: 'Feedback.dc.html'
  };

  function el(name, props, children) {
    var R = window.React, K = window.Kataki;
    patch();
    if (!R || !K || !K[name]) return null;
    return R.createElement(K[name], props || {}, children);
  }
  function btn(variant, text, more) {
    return el('Button', Object.assign({ key: text, variant: variant }, more || {}), text);
  }

  /* One theme switch for every Sky page: the rail's Day / Night item flips the page it is on. */
  function page(self, extra) {
    patch();
    var st = self.state || {};
    var theme = st.theme || self.props.theme || 'night';
    var base = {
      theme: theme,
      yes: true, no: false,
      hrefs: HREFS,
      nav: function (to) {
        if (to === 'Day') self.setState({ theme: 'day' });
        if (to === 'Night') self.setState({ theme: 'night' });
      }
    };
    return Object.assign(base, extra || {});
  }

  window.KApp = { art: function (k) { return '/_blob/' + ART[k]; }, hrefs: HREFS, el: el, btn: btn, page: page, patch: patch };
})();
