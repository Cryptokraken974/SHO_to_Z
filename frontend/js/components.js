/**
 * Component System for LAZ Terrain Processor
 * Provides modular HTML components for better maintainability
 */

class ComponentManager {
    constructor() {
        this.components = new Map();
        this.rendered = new Map();
    }

    /**
     * Register a new component
     * @param {string} name - Component name
     * @param {function} template - Function that returns HTML string
     * @param {object} options - Component options
     */
    register(name, template, options = {}) {
        this.components.set(name, {
            template,
            options,
            dependencies: options.dependencies || []
        });
    }

    /**
     * Render a component to a target element
     * @param {string} name - Component name
     * @param {string|HTMLElement} target - Target element or selector
     * @param {object} props - Props to pass to the component
     */
    async render(name, target, props = {}) {
        const component = this.components.get(name);
        if (!component) {
            throw new Error(`Component '${name}' not found`);
        }

        // Resolve dependencies first
        for (const dep of component.dependencies) {
            if (!this.rendered.has(dep)) {
                console.warn(`Dependency '${dep}' not rendered for component '${name}'`);
            }
        }

        // Get target element
        const targetEl = typeof target === 'string' ? document.querySelector(target) : target;
        if (!targetEl) {
            throw new Error(`Target element not found: ${target}`);
        }

        // Render component
        const html = await component.template(props);
        targetEl.innerHTML = html;

        // Mark as rendered
        this.rendered.set(name, { target: targetEl, props });

        // Execute post-render callback if provided
        if (component.options.onRender) {
            component.options.onRender(targetEl, props);
        }

        return targetEl;
    }

    /**
     * Update a rendered component with new props
     * @param {string} name - Component name
     * @param {object} newProps - New props
     */
    async update(name, newProps = {}) {
        const rendered = this.rendered.get(name);
        if (!rendered) {
            throw new Error(`Component '${name}' not rendered yet`);
        }

        const mergedProps = { ...rendered.props, ...newProps };
        await this.render(name, rendered.target, mergedProps);
    }

    /**
     * Get a rendered component's element
     * @param {string} name - Component name
     * @returns {HTMLElement|null}
     */
    getElement(name) {
        const rendered = this.rendered.get(name);
        return rendered ? rendered.target : null;
    }
}

// Global component manager instance
window.componentManager = new ComponentManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComponentManager;
}
