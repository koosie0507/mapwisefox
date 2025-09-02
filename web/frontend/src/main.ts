import React from "react";
import {createRoot} from "react-dom/client";

const modules = import.meta.glob("./pages/*.tsx"); // lazy by default
type Mount = (el: Element, props?: unknown) => Promise<void>;
const registry = new Map<string, Mount>();

for (const [path, loader] of Object.entries(modules)) {
    const name = path.match(/([^/]+)\.tsx$/)![1]; // e.g., HelloWidget
    registry.set(name, async (el, props) => {
        const mod: any = await loader();                 // code-split chunk
        const Cmp = mod.default ?? mod[name] ?? mod[Object.keys(mod)[0]];
        // @ts-expect-error JSX at runtime
        createRoot(el).render(React.createElement(Cmp, props));
    });
}

function mountAll() {
    console.log("mount all");
    document.querySelectorAll<HTMLElement>("[data-widget]").forEach((el) => {
        const name = el.dataset.widget!;
        const raw = el.dataset.props;
        console.log(raw)
        const props = raw ? JSON.parse(raw) : undefined;
        console.log(props);
        const mount = registry.get(name);
        if (mount) {
            mount(el, props).catch(console.error);
        }
    });
}

Object.assign(window, {mountAll});
