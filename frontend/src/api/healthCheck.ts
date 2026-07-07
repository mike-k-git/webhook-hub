export const healthCheck = async () => {
  const healthCheckResponse = await fetch("/api/healthz");
  const status = await healthCheckResponse.json();
  return status;
};
