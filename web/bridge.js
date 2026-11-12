/**
 * Whiteboard Bridge: Real-time client for Whiteboard AI Agent.
 * Direct pen/marker drawings: Zero UI cards, zero window borders.
 */
class WhiteboardBridge {
  constructor(options = {}) {
    this.boardEl = options.boardEl || document.getElementById('board');
    this.worldEl = options.worldEl || document.getElementById('world');
    this.svgInkEl = options.svgInkEl || document.getElementById('ink');
    this.wsUrl = options.wsUrl || `ws://${window.location.host}/ws`;
    this.apiUrl = options.apiUrl || `http://${window.location.host}`;
    this.showSpatialBounds = false;
    this.elements = new Map();
    this.viewport = { x: 0, y: 0, zoom: 1.0 };
    this.onStateChange = options.onStateChange || null;

    this.initSocket();
  }

  initSocket() {
    try {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => {
        const st = document.getElementById('conn-status');
        if (st) st.textContent = 'Live Drawing';
      };
      this.ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          this.handleServerMessage(msg);
        } catch (err) {}
      };
      this.ws.onclose = () => {
        const st = document.getElementById('conn-status');
        if (st) st.textContent = 'Reconnecting...';
        setTimeout(() => this.initSocket(), 2000);
      };
    } catch (err) {
      console.warn('Socket error:', err);
    }
  }

  handleServerMessage(msg) {
    if (msg.event === 'init_state') {
      const data = msg.data;
      if (data.elements) {
        this.clearAll();
        Object.values(data.elements).forEach((el) => this.renderElement(el));
      }
      if (window.fitView) window.fitView();
    } else if (msg.event === 'tool_executed') {
      this.fetchState().then(() => {
        if (window.fitView) window.fitView();
      });
    }
    if (this.onStateChange) this.onStateChange(msg);
  }

  async fetchState() {
    try {
      const r = await fetch(`${this.apiUrl}/api/state`);
      const data = await r.json();
      this.clearAll();
      Object.values(data.elements).forEach((el) => this.renderElement(el));
      if (this.onStateChange) this.onStateChange(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch state:', err);
    }
  }

  async executeTool(tool, args = {}) {
    try {
      const r = await fetch(`${this.apiUrl}/api/tools/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool, arguments: args })
      });
      const res = await r.json();
      await this.fetchState();
      return res;
    } catch (err) {
      console.error('Execute tool error:', err);
      return { success: false, error: String(err) };
    }
  }

  clearAll() {
    this.elements.clear();
    if (this.worldEl) {
      const objs = this.worldEl.querySelectorAll('.wb-obj');
      objs.forEach((o) => o.remove());
    }
    if (this.svgInkEl) {
      this.svgInkEl.replaceChildren();
    }
  }

  setViewport(vp, animate = false) {
    this.viewport = { ...this.viewport, ...vp };
    if (!this.worldEl) return;
    this.worldEl.classList.toggle('no-anim', !animate);
    const s = this.viewport.zoom;
    this.worldEl.style.transform = `translate(${this.viewport.x}px, ${this.viewport.y}px) scale(${s})`;
  }

  renderElement(el) {
    this.elements.set(el.id, el);

    // Strokes (underlines, circles, arrows, lines) render as pure pen ink in SVG layer
    if (el.type === 'stroke') {
      this.renderStroke(el);
      return;
    }

    // DOM Ink Elements: Rendered DIRECTLY onto the canvas with ZERO card wrapper
    const dom = document.createElement('div');
    dom.id = el.id;
    dom.className = `wb-obj wb-${el.type}` + (this.showSpatialBounds ? ' wb-debug-box' : '');
    dom.style.left = `${el.bounds.x}px`;
    dom.style.top = `${el.bounds.y}px`;
    dom.style.width = `${el.bounds.width}px`;

    let html = '';

    if (el.type === 'formula') {
      const f = el.content?.formula || '';
      const steps = el.content?.steps || [];
      const stepsHtml = steps.map((s) => `<div class="ink-step">• ${s}</div>`).join('');
      html = `
        <div class="ink-formula-wrap">
          <div class="ink-math">${f}</div>
          ${steps.length ? `<div class="ink-steps">${stepsHtml}</div>` : ''}
        </div>
      `;
    } else if (el.type === 'text') {
      html = `<div class="ink-text">${el.content || el.title}</div>`;
    } else if (el.type === 'sticky_note') {
      html = `
        <div class="ink-note">
          ${el.title ? `<div class="ink-note-title">${el.title}</div>` : ''}
          <div>${el.content}</div>
        </div>
      `;
    } else if (el.type === 'mermaid' || (el.type === 'diagram' && el.content?.mermaid_code)) {
      const mCode = el.content?.mermaid_code || el.content?.code || '';
      const targetId = `mrmd-cnt-${el.id.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
      html = `
        <div class="ink-mermaid-wrapper">
          ${el.title ? `<div class="ink-mermaid-title">${el.title}</div>` : ''}
          <div id="${targetId}" class="mermaid-diagram-box">
            <span style="font-family:'Patrick Hand',cursive; color:#64748b; font-size:18px;">Rendering diagram...</span>
          </div>
        </div>
      `;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);

      // Render via Mermaid
      const renderDiagram = () => {
        if (window.mermaid) {
          try {
            mermaid.initialize({
              startOnLoad: false,
              theme: 'neutral',
              securityLevel: 'loose',
              fontFamily: 'Patrick Hand, Caveat, sans-serif'
            });
            const svgId = `svg-${targetId}`;
            mermaid.render(svgId, mCode).then(({ svg }) => {
              const box = document.getElementById(targetId);
              if (box) {
                box.innerHTML = svg;
                const svgEl = box.querySelector('svg');
                if (svgEl) {
                  svgEl.style.maxWidth = '100%';
                  svgEl.style.height = 'auto';
                  svgEl.style.background = 'transparent';
                }
              }
            }).catch(err => {
              console.warn('Mermaid render error:', err);
              const box = document.getElementById(targetId);
              if (box) {
                box.innerHTML = `<div style="color:#ef4444; font-family:'Fira Code',monospace; font-size:12px; white-space:pre-wrap; background:rgba(254,226,226,0.6); padding:8px; border-radius:6px;"><b>Diagram Syntax Error:</b><br>${mCode}</div>`;
              }
            });
          } catch (e) {
            console.warn('Mermaid call failed:', e);
          }
        } else {
          setTimeout(renderDiagram, 100);
        }
      };
      renderDiagram();
      return;
    } else if (el.type === 'diagram') {
      if (el.content?.svg) {
        html = el.content.svg;
      } else {
        const nodes = el.content?.nodes || [];
        const nodesHtml = nodes.map((n, i) =>
          `<div class="ink-node-box">${n.label || n.text || JSON.stringify(n)}</div>` +
          (i < nodes.length - 1 ? '<div class="ink-down-arrow">↓</div>' : '')
        ).join('');
        html = `
          <div class="ink-diagram">
            ${el.title ? `<div class="ink-text" style="font-size:24px; color:#1d4ed8; margin-bottom:4px;">${el.title}</div>` : ''}
            ${nodesHtml}
          </div>
        `;
      }
    } else if (el.type === 'graph') {
      const eq = el.content?.equation || 'y = x²';
      html = `
        <div>
          <div class="ink-graph-title">${el.title || eq}</div>
          <svg viewBox="0 0 240 120" style="width:100%; height:110px; overflow:visible;">
            <line x1="10" y1="90" x2="230" y2="90" stroke="#475569" stroke-width="2.5" stroke-linecap="round"/>
            <polygon points="230,86 238,90 230,94" fill="#475569"/>
            <line x1="120" y1="10" x2="120" y2="110" stroke="#475569" stroke-width="2.5" stroke-linecap="round"/>
            <polygon points="116,10 120,2 124,10" fill="#475569"/>
            <text x="228" y="80" font-family="Caveat, cursive" font-size="20" fill="#475569">x</text>
            <text x="128" y="16" font-family="Caveat, cursive" font-size="20" fill="#475569">y</text>
            <path d="M25 90 Q120 10 215 90" fill="none" stroke="#7e22ce" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      `;
    } else if (el.type === 'annotation') {
      html = `<div class="ink-annotation">${el.content}</div>`;
    } else if (el.type === 'hint') {
      html = `<div class="ink-text" style="font-size:24px; color:#b45309;">Note: ${el.content}</div>`;
    } else {
      html = `<div class="ink-text">${el.content}</div>`;
    }

    if (this.showSpatialBounds) {
      html += `<div class="wb-debug-tag">${el.id}</div>`;
    }

    dom.innerHTML = html;
    this.worldEl.appendChild(dom);
  }

  renderStroke(el) {
    if (!this.svgInkEl) return;
    const existing = document.getElementById(el.id);
    if (existing) {
      if (el.content?.svg_fragment) {
        existing.innerHTML = el.content.svg_fragment;
      } else if (el.content?.svg_path) {
        if (existing.tagName.toLowerCase() === 'path') {
          existing.setAttribute('d', el.content.svg_path);
        } else {
          const pathEl = existing.querySelector('path');
          if (pathEl) {
            pathEl.setAttribute('d', el.content.svg_path);
          }
        }
      }
      return;
    }
    if (el.content?.svg_fragment) {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('id', el.id);
      g.innerHTML = el.content.svg_fragment;
      this.svgInkEl.appendChild(g);
      return;
    }
    const svgPath = el.content?.svg_path;
    if (!svgPath) return;

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('id', el.id);
    path.setAttribute('d', svgPath);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', el.style?.color || '#dc2626');
    path.setAttribute('stroke-width', el.style?.stroke_width || 3.5);
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');

    if (el.style?.dash) {
      path.setAttribute('stroke-dasharray', el.style.dash.join(' '));
    }
    this.svgInkEl.appendChild(path);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { WhiteboardBridge };
}
