namespace VisuLecture.Components.Model;

public class Reading
{
    public string Id { get; set; }
    public DateTime Date { get; set; }
    public string StudentId { get; set; }
    public string TextId { get; set; }
    
    // Relations de navigation
    public Student? Student { get; set; }
    public TextRecord? TextRecord { get; set; }
    
    public Reading()
    {
        Id = Guid.NewGuid().ToString("N");
        Date = DateTime.Now;
        StudentId = "";
        TextId = "";
    }

    public Reading(string studentId, string textId)
    {
        Id = Guid.NewGuid().ToString("N");
        Date = DateTime.Now;
        StudentId = studentId;
        TextId = textId;
    }
}

