import React from "react";
import {createRoot} from "react-dom/client";

const modules = import.meta.glob("./pages/*.tsx"); // lazy by default
type Mount = (el: Element, props?: unknown) => Promise<void>;
const registry = new Map<string, Mount>();

for (const [path, loader] of Object.entries(modules)) {
    const name = path.match(/([^/]+)\.tsx$/)![1]; // e.g., HelloWidget
    registry.set(name, async (el, props) => {
        const mod = await loader() as Record<string, React.ComponentType<Record<string, unknown>>>;
        const Cmp = mod.default ?? mod[name] ?? mod[Object.keys(mod)[0]];
        createRoot(el).render(React.createElement(Cmp, (props ?? {}) as Record<string, unknown>));
    });
}

function mountAll() {
    document.querySelectorAll<HTMLElement>("[data-widget]").forEach((el) => {
        const name = el.dataset.widget!;
        const raw = el.dataset.props;
        const props = raw ? JSON.parse(raw) : undefined;
        const mount = registry.get(name);
        if (mount) {
            mount(el, props).catch(console.error);
        }
    });
}

Object.assign(window, {mountAll});
