export default function Hello({ name = "World" }: { name?: string }) {
  return <strong>Hello, {name} 👋</strong>;
}
