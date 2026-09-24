// frontend/src/hooks/useShipment.ts
import { createContext, useContext, useState, ReactNode } from 'react';

interface ShipmentContextValue {
  shipmentId: string | null;
  setShipmentId: (id: string) => void;
}

const ShipmentContext = createContext<ShipmentContextValue>({
  shipmentId: null,
  setShipmentId: () => {},
});

export function ShipmentProvider({ children }: { children: ReactNode }) {
  const [shipmentId, setShipmentId] = useState<string | null>(
    () => sessionStorage.getItem('clearancex_shipment_id')
  );

  const handleSet = (id: string) => {
    setShipmentId(id);
    sessionStorage.setItem('clearancex_shipment_id', id);
  };

  return (
    <ShipmentContext.Provider value={{ shipmentId, setShipmentId: handleSet }}>
      {children}
    </ShipmentContext.Provider>
  );
}

export function useShipment(): ShipmentContextValue {
  return useContext(ShipmentContext);
}
