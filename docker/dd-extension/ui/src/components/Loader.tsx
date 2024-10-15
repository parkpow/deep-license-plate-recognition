import Spinner from "react-bootstrap/Spinner";

interface LoaderProps {
  isLoading: boolean;

}

export default function Loader({ isLoading }: LoaderProps) {
  if (!isLoading) return null;
  return (
    <Spinner animation="border" role="status" size='sm'>
      <span className="visually-hidden">Loading...</span>
    </Spinner>
  );
}
