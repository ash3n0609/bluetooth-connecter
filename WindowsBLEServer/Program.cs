using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Devices.Bluetooth.GenericAttributeProfile;
using Windows.Storage.Streams;

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("Windows .NET BLE Broadcaster Booting...");
        
        string dataFilePath = Path.Combine(Directory.GetParent(Directory.GetCurrentDirectory()).FullName, "windows_ecg_data.txt");
        
        if (!File.Exists(dataFilePath)) {
            Console.WriteLine($"Critical Error: Could not find pure data text file at {dataFilePath}");
            return;
        }

        double[] ecgData = File.ReadAllLines(dataFilePath).Select(double.Parse).ToArray();
        Console.WriteLine($"Successfully loaded {ecgData.Length} telemetry points into C# memory pool.");

        Guid serviceUuid = Guid.Parse("12345678-1234-5678-1234-56789abcdef0");
        Guid charUuid    = Guid.Parse("abcdef01-1234-5678-1234-56789abcdef0");

        var serviceProviderResult = await GattServiceProvider.CreateAsync(serviceUuid);
        if (serviceProviderResult.Error != Windows.Devices.Bluetooth.BluetoothError.Success)
        {
            Console.WriteLine($"Failed to bind GATT Service Provider. Error: {serviceProviderResult.Error}");
            return;
        }

        var serviceProvider = serviceProviderResult.ServiceProvider;

        var charParameters = new GattLocalCharacteristicParameters
        {
            CharacteristicProperties = GattCharacteristicProperties.Read | GattCharacteristicProperties.Notify,
            ReadProtectionLevel = GattProtectionLevel.Plain,
        };

        var charResult = await serviceProvider.Service.CreateCharacteristicAsync(charUuid, charParameters);
        if (charResult.Error != Windows.Devices.Bluetooth.BluetoothError.Success)
        {
            Console.WriteLine($"Failed to create GATT Characteristic. Error: {charResult.Error}");
            return;
        }

        var characteristic = charResult.Characteristic;

        // Windows strictly uses the PC Hostname for BLE Advertisements and doesn't allow overriding here securely.
        var advParameters = new GattServiceProviderAdvertisingParameters
        {
            IsDiscoverable = true,
            IsConnectable = true
        };
        
        serviceProvider.StartAdvertising(advParameters);
        Console.WriteLine($"Windows GATT Broadcasting Active!");
        Console.WriteLine($"Note: Your device will appear as '{Environment.MachineName}' or generic, but the receiver will lock onto the hidden Service UUID.");
        Console.WriteLine("Press Ctrl+C to stop.");

        try {
            int index = 0;
            while (true)
            {
                double val = ecgData[index % ecgData.Length];
                
                var writer = new DataWriter();
                // Match the struct.pack('<d') Python signature precisely
                writer.ByteOrder = ByteOrder.LittleEndian;
                writer.WriteDouble(val);

                // Fire the telemetry off the Bluetooth radio asynchronously 
                await characteristic.NotifyValueAsync(writer.DetachBuffer());
                
                index++;
                await Task.Delay(100);
            }
        } 
        catch (Exception ex) {
            Console.WriteLine($"Fatal runtime crash: {ex.Message}");
        }
        finally {
            serviceProvider.StopAdvertising();
        }
    }
}
