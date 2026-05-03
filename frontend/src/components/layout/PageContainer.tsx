import type { PropsWithChildren } from "react";

export default function PageContainer({ children }: PropsWithChildren) {
  return <div className="page-container">{children}</div>;
}
