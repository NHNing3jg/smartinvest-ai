type ErrorMessageProps = {
  title?: string;
  message: string;
};

export default function ErrorMessage({ title = "Something went wrong", message }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
