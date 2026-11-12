/**
 * Whiteboard Bridge: Real-time client for Whiteboard AI Agent.
 * Direct pen/marker drawings: Zero UI cards, zero window borders.
 * Smooth typewriter effect for newly drawn text & equations.
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
    this.renderedIds = new Set();
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
      const incoming = data.elements || {};
      const incomingIds = new Set(Object.keys(incoming));

      // Remove elements that are no longer in server state
      for (const [id] of this.elements) {
        if (!incomingIds.has(id)) {
          this.removeElement(id);
        }
      }

      // Render new or updated elements
      Object.values(incoming).forEach((el) => this.renderElement(el));
      if (this.onStateChange) this.onStateChange(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch state:', err);
    }
  }

  removeElement(id) {
    this.elements.delete(id);
    this.renderedIds.delete(id);
    const dom = document.getElementById(id);
    if (dom) dom.remove();
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
    this.renderedIds.clear();
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

  /**
   * Smooth natural handwriting / typewriter effect synced with AI Tutor Pen
   */
  typeWrite(element, text, speed = 24, onComplete = null, bounds = null, targetDurationMs = null) {
    if (!element) {
      if (onComplete) onComplete();
      return;
    }
    const str = String(text || '');
    if (!str) {
      element.textContent = '';
      if (onComplete) onComplete();
      return;
    }

    element.textContent = '';
    element.classList.add('ink-typing');
    let idx = 0;
    const len = str.length;

    // Harmonize typing duration with spoken narration tempo
    let stepMs = speed;
    const desiredDur = targetDurationMs || window.activeWritingDurationMs || null;
    if (desiredDur && desiredDur > 0) {
      stepMs = Math.max(14, Math.min(55, Math.floor(desiredDur / Math.max(1, len))));
    } else {
      stepMs = Math.max(12, Math.min(35, Math.floor(1000 / Math.max(1, len))));
    }

    if (window.setTutorPenState) {
      window.setTutorPenState('writing');
    }

    const timer = setInterval(() => {
      idx++;
      element.textContent = str.slice(0, idx);

      if (window.onTutorTypingProgress && bounds) {
        window.onTutorTypingProgress(bounds, idx / len);
      }

      if (idx >= len) {
        clearInterval(timer);
        element.classList.remove('ink-typing');
        if (window.setTutorPenState) {
          window.setTutorPenState('pointing');
        }
        if (onComplete) onComplete();
      }
    }, stepMs);
  }

  /**
   * Sanitizes Mermaid code to avoid parser lexer crashes
   */
  sanitizeMermaidCode(raw) {
    if (!raw) return 'graph TD\n  Node["Whiteboard Diagram"]';
    let code = raw.trim();
    // Remove markdown code fences
    code = code.replace(/^```(?:mermaid)?\n?/i, '').replace(/\n?```$/i, '').trim();

    // Ensure diagram declaration
    if (!/^(graph|flowchart|sequenceDiagram|stateDiagram|classDiagram|erDiagram|gitGraph|journey|mindmap)\b/i.test(code)) {
      code = 'graph TD\n' + code;
    }

    // Replace unencoded < and > inside edge labels |...| with &lt; and &gt;
    code = code.replace(/(\|)([^|\n]+)(\|)/g, (match, p1, p2, p3) => {
      let label = p2.trim();
      label = label.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return `${p1}${label}${p3}`;
    });

    return code;
  }

  /**
   * Native Dry-Erase Whiteboard Diagram Fallback
   * Guarantees student NEVER sees a red syntax error card.
   */
  renderNativeWhiteboardDiagram(targetBox, code) {
    if (!targetBox) return;
    const lines = code.split('\n')
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith('graph') && !l.startsWith('flowchart') && !l.startsWith('%%'));

    const nodes = [];
    lines.forEach((line) => {
      const parts = line.split(/-->(?:\|[^|]+\|)?|\.->|==>/);
      parts.forEach((p) => {
        const clean = p.replace(/[[\]{}()"]/g, '').trim();
        if (clean && !nodes.includes(clean)) nodes.push(clean);
      });
    });

    if (nodes.length === 0) nodes.push('Flow Concept', 'Key Step', 'Result');

    const nodesHtml = nodes.map((n, i) => `
      <div style="display:inline-flex; align-items:center; margin: 4px 6px;">
        <span style="font-family:'Patrick Hand',cursive; font-size:22px; color:#1e293b; padding:4px 12px; border:2px solid #3b82f6; border-radius:9999px; background:rgba(255,255,255,0.7);">${n}</span>
        ${i < nodes.length - 1 ? '<span style="font-family:\'Caveat\',cursive; font-size:24px; color:#2563eb; margin:0 8px;">&rarr;</span>' : ''}
      </div>
    `).join('');

    targetBox.innerHTML = `
      <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; padding:12px; width:100%;">
        ${nodesHtml}
      </div>
    `;
  }

  renderElement(el) {
    const isNew = !this.renderedIds.has(el.id);
    this.elements.set(el.id, el);

    // Strokes (underlines, circles, arrows, lines) render as pure pen ink in SVG layer
    if (el.type === 'stroke') {
      this.renderStroke(el, isNew);
      return;
    }

    // If element already exists in DOM, update position/bounds
    let dom = document.getElementById(el.id);
    if (dom && !isNew) {
      dom.style.left = `${el.bounds.x}px`;
      dom.style.top = `${el.bounds.y}px`;
      dom.style.width = `${el.bounds.width}px`;
      return;
    }

    this.renderedIds.add(el.id);

    // DOM Ink Elements: Rendered DIRECTLY onto the canvas with ZERO card wrapper
    dom = document.createElement('div');
    dom.id = el.id;
    dom.className = `wb-obj wb-${el.type}` + (this.showSpatialBounds ? ' wb-debug-box' : '');
    dom.style.left = `${el.bounds.x}px`;
    dom.style.top = `${el.bounds.y}px`;
    dom.style.width = `${el.bounds.width}px`;
    if (el.type === 'formula') {
      dom.style.whiteSpace = 'nowrap';
      dom.style.minWidth = `${el.bounds.width}px`;
      dom.style.width = 'max-content';
    }

    const syncBounds = () => {
      requestAnimationFrame(() => {
        if (!dom || !el || !el.bounds) return;
        const rect = dom.getBoundingClientRect();
        const zoom = this.viewport?.zoom || 1.0;
        if (rect.width > 0 && rect.height > 0) {
          const realW = Math.round(rect.width / zoom);
          const realH = Math.round(rect.height / zoom);
          if (realW > el.bounds.width) el.bounds.width = realW;
          if (realH > el.bounds.height) el.bounds.height = realH;
        }
      });
    };

    let html = '';

    if (el.type === 'formula') {
      const f = el.content?.formula || '';
      const steps = el.content?.steps || [];
      const stepsHtml = steps.map((s) => `<div class="ink-step">• ${s}</div>`).join('');
      html = `
        <div class="ink-formula-wrap">
          <div class="ink-math"></div>
          ${steps.length ? `<div class="ink-steps">${stepsHtml}</div>` : ''}
        </div>
      `;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();

      const mathEl = dom.querySelector('.ink-math');
      if (isNew && mathEl) {
        this.typeWrite(mathEl, f, 24, null, el.bounds);
      } else if (mathEl) {
        mathEl.textContent = f;
      }
      return;
    } else if (el.type === 'text') {
      html = `<div class="ink-text"></div>`;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();

      const txtEl = dom.querySelector('.ink-text');
      const textToType = el.content || el.title || '';
      if (isNew && txtEl) {
        this.typeWrite(txtEl, textToType, 20, null, el.bounds);
      } else if (txtEl) {
        txtEl.textContent = textToType;
      }
      return;
    } else if (el.type === 'sticky_note') {
      html = `
        <div class="ink-note">
          ${el.title ? `<div class="ink-note-title">${el.title}</div>` : ''}
          <div class="ink-note-body"></div>
        </div>
      `;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();

      const bodyEl = dom.querySelector('.ink-note-body');
      const contentToType = el.content || '';
      if (isNew && bodyEl) {
        this.typeWrite(bodyEl, contentToType, 20, null, el.bounds);
      } else if (bodyEl) {
        bodyEl.textContent = contentToType;
      }
      return;
    } else if (el.type === 'mermaid' || (el.type === 'diagram' && el.content?.mermaid_code)) {
      const mCode = el.content?.mermaid_code || el.content?.code || '';
      const targetId = `mrmd-cnt-${el.id.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
      html = `
        <div class="ink-mermaid-wrapper">
          ${el.title ? `<div class="ink-mermaid-title">${el.title}</div>` : ''}
          <div id="${targetId}" class="mermaid-diagram-box">
            <span style="font-family:'Patrick Hand',cursive; color:#64748b; font-size:18px;">Drawing diagram...</span>
          </div>
        </div>
      `;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();

      const cleanCode = this.sanitizeMermaidCode(mCode);

      // Render via Mermaid with automatic fallback
      const renderDiagram = () => {
        if (window.mermaid) {
          try {
            mermaid.initialize({
              startOnLoad: false,
              theme: 'neutral',
              securityLevel: 'loose',
              fontFamily: 'Patrick Hand, Caveat, sans-serif'
            });
            const svgId = `svg_mrmd_${Math.random().toString(36).substring(2, 9)}`;
            mermaid.render(svgId, cleanCode).then(({ svg }) => {
              const box = document.getElementById(targetId);
              if (box) {
                box.innerHTML = svg;
                const svgEl = box.querySelector('svg');
                if (svgEl) {
                  svgEl.style.maxWidth = '100%';
                  svgEl.style.height = 'auto';
                  svgEl.style.background = 'transparent';
                  requestAnimationFrame(() => {
                    const rect = dom.getBoundingClientRect();
                    const zoom = this.viewport?.zoom || 1.0;
                    if (rect.height > 0) {
                      el.bounds.height = Math.max(el.bounds.height, Math.round(rect.height / zoom));
                      el.bounds.width = Math.max(el.bounds.width, Math.round(rect.width / zoom));
                    }
                  });
                }
              }
            }).catch((err) => {
              console.warn('Mermaid render error, switching to native diagram:', err);
              const box = document.getElementById(targetId);
              if (box) {
                this.renderNativeWhiteboardDiagram(box, cleanCode);
              }
            });
          } catch (e) {
            console.warn('Mermaid call failed, rendering native diagram:', e);
            const box = document.getElementById(targetId);
            if (box) {
              this.renderNativeWhiteboardDiagram(box, cleanCode);
            }
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
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();
      return;
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
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();
      return;
    } else if (el.type === 'hint') {
      html = `<div class="ink-text" style="color:#b45309;"><span class="ink-hint-icon font-bold">Note: </span><span class="ink-hint-body"></span></div>`;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();

      const hBody = dom.querySelector('.ink-hint-body');
      if (isNew && hBody) {
        this.typeWrite(hBody, el.content || '', 20);
      } else if (hBody) {
        hBody.textContent = el.content || '';
      }
      return;
    } else {
      html = `<div class="ink-text"></div>`;
      dom.innerHTML = html;
      this.worldEl.appendChild(dom);
      syncBounds();

      const tEl = dom.querySelector('.ink-text');
      if (isNew && tEl) {
        this.typeWrite(tEl, el.content || '', 20);
      } else if (tEl) {
        tEl.textContent = el.content || '';
      }
      return;
    }
  }

  renderStroke(el, isNew = true) {
    if (!this.svgInkEl) return;
    this.renderedIds.add(el.id);

    // If stroke already exists, update coordinates and SVG path
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

    // Natural drawing stroke animation synced with AI Tutor Pen
    if (isNew && path.getTotalLength) {
      try {
        const length = path.getTotalLength();
        if (length > 0) {
          if (window.animateTutorStroke) {
            window.animateTutorStroke(path, length);
          } else {
            path.style.strokeDasharray = `${length}`;
            path.style.strokeDashoffset = `${length}`;
            path.getBoundingClientRect(); // trigger reflow
            path.style.transition = 'stroke-dashoffset 0.75s ease-out';
            path.style.strokeDashoffset = '0';
          }
        }
      } catch (e) {}
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { WhiteboardBridge };
}
