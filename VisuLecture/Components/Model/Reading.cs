namespace VisuLecture.Components.Model;

public class Reading
{
    public string Id { get; set; }
    public DateTime Date { get; set; }
    public string StudentId { get; set; }
    public string TextId { get; set; }
    
    // Dimensions de l'écran utilisateur
    public int ScreenWidth { get; set; }
    public int ScreenHeight { get; set; }
    
    // Dimensions de la vidéo de la caméra
    public int VideoWidth { get; set; }
    public int VideoHeight { get; set; }
    
    // Relations de navigation
    public Student? Student { get; set; }
    public TextRecord? TextRecord { get; set; }
    
    public Reading()
    {
        Id = Guid.NewGuid().ToString("N");
        Date = DateTime.Now;
        StudentId = "";
        TextId = "";
        ScreenWidth = 0;
        ScreenHeight = 0;
        VideoWidth = 0;
        VideoHeight = 0;
    }

    public Reading(string studentId, string textId)
    {
        Id = Guid.NewGuid().ToString("N");
        Date = DateTime.Now;
        StudentId = studentId;
        TextId = textId;
        ScreenWidth = 0;
        ScreenHeight = 0;
        VideoWidth = 0;
        VideoHeight = 0;
    }
}

