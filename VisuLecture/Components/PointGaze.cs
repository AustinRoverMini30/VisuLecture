using System.Runtime.InteropServices.Swift;

namespace VisuLecture.Components;

public class PointGaze
{
    public double timestamp;
    public double x;
    public double y;

    public PointGaze(double timestamp, double x, double y, bool jump = false)
    {
        this.timestamp = timestamp;
        this.x = x;
        this.y = y;
    }

    public (double timestamp, double x, double y) getTuple()
    {
        return (this.timestamp, this.x, this.y);
    }
    
    public (double x, double y) getCoord()
    {
        return (this.x, this.y);
    }
    
}