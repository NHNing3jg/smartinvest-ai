type LoaderProps = {
  label?: string;
};

export default function Loader({ label = "Loading" }: LoaderProps) {
  return (
    <div className="loader" role="status" aria-live="polite">
      <span />
      {label}
    </div>
  );
}
